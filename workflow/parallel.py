"""
Parallel workflow for JPEG2000 processing.

This module provides a parallel implementation of the JPEG2000 workflow
using multiprocessing for improved performance.
"""

import os
import gc
import time
import logging
import multiprocessing
import queue
import threading
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Tuple, Set
from functools import partial

from core.types import (
    WorkflowStatus,
    DocumentType,
    CompressionMode,
    ProcessingResult,
    WorkflowConfig,
    BnFCompressionRatio
)
from utils.image import validate_image, get_output_path, find_image_files
from utils.resource_monitor import ResourceMonitor
from workflow.base import BaseWorkflow
from workflow.standard import StandardWorkflow
from core.metadata.bnf_handler import BnFMetadataHandler

logger = logging.getLogger(__name__)


# Define a standalone function outside the class
# This avoids pickling issues by not capturing any class instance state
def standalone_process_file_worker(
    input_file: str,
    output_dir: str,
    report_dir: str,
    doc_type: DocumentType,
    quality_threshold: float,
    num_resolutions: int,
    progression_order: str,
    compression_mode: CompressionMode,
    lossless_fallback: bool,
    bnf_compliant: bool,
    compression_ratio_tolerance: float,
    include_bnf_markers: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a single file without requiring class instance state.
    This standalone function can be pickled and passed to multiprocessing.

    Args:
        input_file: Path to input file
        output_dir: Directory for output files
        report_dir: Directory for reports
        doc_type: Document type for compression
        quality_threshold: PSNR threshold for quality control
        num_resolutions: Number of resolution levels
        progression_order: Progression order for JPEG2000
        compression_mode: Compression mode
        lossless_fallback: Whether to fall back to lossless compression
        bnf_compliant: Whether to use BnF compliant settings
        compression_ratio_tolerance: Tolerance for compression ratio
        include_bnf_markers: Whether to include BnF robustness markers
        metadata: Additional metadata to include in output file

    Returns:
        dict: Processing result as a dictionary
    """
    try:
        # Create a minimal config for the workflow
        config = WorkflowConfig(
            output_dir=output_dir,
            report_dir=report_dir,
            document_type=doc_type,
            quality_threshold=quality_threshold,
            num_resolutions=num_resolutions,
            progression_order=progression_order,
            compression_mode=compression_mode,
            lossless_fallback=lossless_fallback
        )

        # Create a fresh workflow instance specific to this worker
        workflow = StandardWorkflow(config)

        # Default metadata if none provided
        if metadata is None:
            metadata = {}

        # Process the file
        result = workflow._process_file_implementation(
            input_file=input_file,
            doc_type=doc_type,
            lossless_fallback=lossless_fallback,
            bnf_compliant=bnf_compliant,
            compression_ratio_tolerance=compression_ratio_tolerance,
            include_bnf_markers=include_bnf_markers,
            metadata=metadata
        )

        # Calculate file size metrics
        file_sizes = {}
        if hasattr(result, 'file_sizes') and result.file_sizes:
            file_sizes = result.file_sizes
        elif result.output_file and os.path.exists(result.output_file) and os.path.exists(input_file):
            # Calculate file sizes if not available but files exist
            original_size = os.path.getsize(input_file)
            converted_size = os.path.getsize(result.output_file)

            # Format sizes into human-readable format
            original_size_human = format_file_size(original_size)
            converted_size_human = format_file_size(converted_size)

            # Calculate compression ratio
            compression_ratio = f"{original_size / converted_size:.2f}:1" if converted_size > 0 else "N/A"

            file_sizes = {
                "original_size": original_size,
                "original_size_human": original_size_human,
                "converted_size": converted_size,
                "converted_size_human": converted_size_human,
                "compression_ratio": compression_ratio
            }

        # Convert ProcessingResult to dictionary for serialization
        return {
            'input_file': result.input_file,
            'status': result.status.name,
            'output_file': result.output_file,
            'report_file': result.report_file,
            'error': result.error,
            'metrics': result.metrics,
            'file_sizes': file_sizes
        }
    except Exception as e:
        # Return error result if processing fails
        return {
            'input_file': input_file,
            'status': WorkflowStatus.FAILURE.name,
            'output_file': None,
            'report_file': None,
            'error': f"Processing error: {str(e)}",
            'metrics': None,
            'file_sizes': None
        }


def format_file_size(size_in_bytes):
    """Format file size in a human-readable format.

    Args:
        size_in_bytes: Size in bytes

    Returns:
        String with human-readable file size
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


class ParallelWorkflow(BaseWorkflow):
    """Parallel implementation of the JPEG2000 workflow."""

    def __init__(self, config: WorkflowConfig):
        """Initialize the parallel workflow.

        Args:
            config: Workflow configuration
        """
        super().__init__(config)

        # Set up parallel processing
        self.max_workers = config.max_workers or max(1, multiprocessing.cpu_count() - 1)

        # Set up adaptive worker pool if enabled
        self.adaptive_workers = config.adaptive_workers
        self.min_workers = config.min_workers
        self.memory_threshold = config.memory_threshold
        self.cpu_threshold = config.cpu_threshold
        self.memory_limit_mb = config.memory_limit_mb

        # Initialize resource monitor if adaptive workers are enabled
        self.resource_monitor = None
        if self.adaptive_workers:
            self.resource_monitor = ResourceMonitor(
                min_workers=self.min_workers,
                max_workers=self.max_workers,
                memory_threshold=self.memory_threshold,
                cpu_threshold=self.cpu_threshold,
                memory_limit_mb=self.memory_limit_mb
            )

            logger.info(
                f"Using adaptive worker pool: min_workers={self.min_workers}, "
                f"max_workers={self.max_workers}, memory_threshold={self.memory_threshold}, "
                f"cpu_threshold={self.cpu_threshold}"
            )
        else:
            logger.info(f"Using fixed worker pool with {self.max_workers} worker processes")

    def _format_file_size(self, size_in_bytes):
        """Format file size in a human-readable format.

        Args:
            size_in_bytes: Size in bytes

        Returns:
            String with human-readable file size
        """
        return format_file_size(size_in_bytes)

    def _process_file_implementation(
        self,
        input_file: str,
        doc_type: DocumentType,
        lossless_fallback: bool,
        bnf_compliant: bool,
        compression_ratio_tolerance: float,
        include_bnf_markers: bool,
        metadata: Dict[str, Any]
    ) -> ProcessingResult:
        """Implementation of file processing logic.

        Args:
            input_file: Path to input file
            doc_type: Document type for compression
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers
            metadata: Additional metadata to include in output file

        Returns:
            ProcessingResult: Result of processing
        """
        # For ParallelWorkflow, delegate to StandardWorkflow for actual processing
        standard_workflow = StandardWorkflow(self.config)
        return standard_workflow._process_file_implementation(
            input_file=input_file,
            doc_type=doc_type,
            lossless_fallback=lossless_fallback,
            bnf_compliant=bnf_compliant,
            compression_ratio_tolerance=compression_ratio_tolerance,
            include_bnf_markers=include_bnf_markers,
            metadata=metadata
        )

    def _generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report from the processing results.

        Args:
            results: Dictionary with processing results

        Returns:
            Summary report as a string
        """
        summary_lines = []
        summary_lines.append("# JPEG2000 Conversion Summary Report")
        summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        summary_lines.append("## Overall Statistics\n-----------------")
        summary_lines.append(f"Total Files: {len(results.get('processed_files', []))}")
        summary_lines.append(f"Successful: {results.get('success_count', 0)}")
        summary_lines.append(f"Warnings: {results.get('warning_count', 0)}")
        summary_lines.append(f"Errors: {results.get('error_count', 0)}")
        summary_lines.append(f"Corrupted/Skipped: {results.get('corrupted_count', 0)}")

        # Use .name if status is an enum, otherwise use the string value directly
        overall_status = results.get('status', WorkflowStatus.FAILURE)
        if hasattr(overall_status, 'name'):
            summary_lines.append(f"Overall Status: {overall_status.name}")
        else:
            summary_lines.append(f"Overall Status: {overall_status}")

        if results.get('processing_time', 0) > 0:
            processing_time = results['processing_time']
            total_files = len(results.get('processed_files', []))

            summary_lines.append(f"Total Processing Time: {processing_time:.2f} seconds")

            if total_files > 0:
                files_per_second = total_files / processing_time
                summary_lines.append(
                    f"Average Processing Rate: {files_per_second:.2f} files/second")

                # Add worker pool statistics if available
                if self.adaptive_workers and 'avg_workers' in results:
                    avg_workers = results['avg_workers']
                    summary_lines.append(f"Average Worker Count: {avg_workers:.1f}")
                    summary_lines.append(
                        f"Worker Efficiency: {files_per_second / avg_workers:.2f} files/worker/second")

                    # Add worker adjustment chart if statistics are available
                    if 'worker_stats' in results and results['worker_stats']:
                        worker_stats = results['worker_stats']
                        max_stat = max(worker_stats)
                        min_stat = min(worker_stats)

                        # Only add chart if there were worker adjustments
                        if max_stat != min_stat:
                            summary_lines.append("\n## Worker Pool Adjustment\n-----------------")
                            summary_lines.append(
                                "Resource-based scaling adjusted the worker count during processing:")
                            summary_lines.append(f"* Maximum workers: {max_stat}")
                            summary_lines.append(f"* Minimum workers: {min_stat}")
                            summary_lines.append(f"* Average workers: {avg_workers:.1f}")
                            summary_lines.append("")
                else:
                    summary_lines.append(f"Fixed Worker Count: {self.max_workers}")
                    summary_lines.append(
                        f"Worker Efficiency: {files_per_second / self.max_workers:.2f} files/worker/second")

        # Add configuration details
        summary_lines.append("\n## Configuration\n-----------------")
        summary_lines.append(
            f"Processing Mode: {'Parallel with Adaptive Workers' if self.adaptive_workers else 'Parallel with Fixed Workers'}")
        summary_lines.append(f"Max Workers: {self.max_workers}")

        if self.adaptive_workers:
            summary_lines.append(f"Min Workers: {self.min_workers}")
            summary_lines.append(f"Memory Threshold: {self.memory_threshold * 100:.0f}%")
            summary_lines.append(f"CPU Threshold: {self.cpu_threshold * 100:.0f}%")
            summary_lines.append(f"Memory Limit: {self.memory_limit_mb} MB")

        summary_lines.append(f"Compression Mode: {self.config.compression_mode.value}")
        summary_lines.append(f"Document Type: {self.config.document_type.name}")
        summary_lines.append(f"Quality Threshold: {self.config.quality_threshold}")
        summary_lines.append(f"BnF Compliant: {self.config.bnf_compliant}")

        # Add details for each file
        summary_lines.append("\n## Detailed Results\n----------------")

        # Limit to first 20 files to avoid huge reports
        for file_result in results.get('processed_files', [])[:20]:
            input_file = file_result.get('input_file', 'Unknown')
            status = file_result.get('status', 'UNKNOWN')
            output_file = file_result.get('output_file', '')

            summary_lines.append(f"### {os.path.basename(input_file)}")
            summary_lines.append(f"Status: {status}")

            if output_file:
                summary_lines.append(f"Output: {os.path.basename(output_file)}")

            # Add file size information if available
            if 'file_sizes' in file_result and file_result['file_sizes']:
                sizes = file_result['file_sizes']
                summary_lines.append(f"Original Size: {sizes.get('original_size_human', 'N/A')}")
                summary_lines.append(f"Converted Size: {sizes.get('converted_size_human', 'N/A')}")
                summary_lines.append(f"Compression Ratio: {sizes.get('compression_ratio', 'N/A')}")

            # Add error message if present
            if file_result.get('error'):
                summary_lines.append(f"Error: {file_result['error']}")

            summary_lines.append("")

        # Add note if there are more files
        if len(results.get('processed_files', [])) > 20:
            remaining = len(results['processed_files']) - 20
            summary_lines.append(f"... and {remaining} more files (omitted for brevity)")

        # End the report
        summary_lines.append("\n## End of Report")
        summary_lines.append(
            f"Generated by JP2Forge v0.9 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(summary_lines)

    def process_directory(
        self,
        input_dir: str,
        doc_type: Optional[DocumentType] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recursive: Optional[bool] = None,
        lossless_fallback: Optional[bool] = None,
        bnf_compliant: Optional[bool] = None,
        compression_ratio_tolerance: Optional[float] = None,
        include_bnf_markers: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Process all files in a directory using parallel processing.

        Args:
            input_dir: Directory containing input files
            doc_type: Document type for compression
            metadata: Metadata to add to files
            recursive: Whether to process subdirectories
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers

        Returns:
            Dictionary with processing results
        """
        # Validate output directory before processing (implementing BaseWorkflow validation)
        if not self.config.output_dir or not os.path.exists(self.config.output_dir):
            logger.error("Output directory not specified or does not exist")
            return {
                'status': WorkflowStatus.FAILURE,
                'error': 'Output directory not specified or does not exist',
                'processed_files': [],
                'success_count': 0,
                'warning_count': 0,
                'error_count': 1,
                'corrupted_count': 0
            }

        # Use configuration defaults if not specified
        doc_type = doc_type or self.config.document_type
        recursive = self.config.recursive if recursive is None else recursive
        lossless_fallback = (
            self.config.lossless_fallback
            if lossless_fallback is None
            else lossless_fallback
        )
        bnf_compliant = (
            self.config.bnf_compliant
            if bnf_compliant is None
            else bnf_compliant
        )
        compression_ratio_tolerance = (
            self.config.compression_ratio_tolerance
            if compression_ratio_tolerance is None
            else compression_ratio_tolerance
        )
        include_bnf_markers = (
            self.config.include_bnf_markers
            if include_bnf_markers is None
            else include_bnf_markers
        )

        # Initialize default metadata if not provided
        if metadata is None:
            metadata = {}

        if not os.path.exists(input_dir):
            logger.error(f"Input directory not found: '{input_dir}'. Please check the path exists and you have read permissions.")
            return {
                'status': WorkflowStatus.FAILURE,
                'error': f'Input directory not found: {input_dir}. Please check the path exists and you have read permissions.'
            }

        # Initialize results and tracking
        results = {
            'status': WorkflowStatus.SUCCESS,  # Initial status
            'processed_files': [],
            'success_count': 0,
            'warning_count': 0,
            'error_count': 0,
            'corrupted_count': 0,
            'processing_time': 0,
            'max_workers': self.max_workers
        }

        # Initialize tracking variables
        self.processed_files_count = 0
        self.start_time = time.time()

        # Find all image files to process
        image_files = find_image_files(input_dir, recursive)

        self.total_files = len(image_files)
        logger.info(f"Found {self.total_files} image files to process")

        if self.adaptive_workers:
            # Use adaptive worker pool
            results = self._process_with_adaptive_workers(
                image_files=image_files,
                doc_type=doc_type,
                lossless_fallback=lossless_fallback,
                bnf_compliant=bnf_compliant,
                compression_ratio_tolerance=compression_ratio_tolerance,
                include_bnf_markers=include_bnf_markers,
                metadata=metadata
            )
        else:
            # Use fixed worker pool
            results = self._process_with_fixed_workers(
                image_files=image_files,
                doc_type=doc_type,
                lossless_fallback=lossless_fallback,
                bnf_compliant=bnf_compliant,
                compression_ratio_tolerance=compression_ratio_tolerance,
                include_bnf_markers=include_bnf_markers,
                metadata=metadata
            )

        # Generate summary report
        summary_report = self._generate_summary_report(results)
        summary_file = os.path.join(self.config.report_dir, 'summary_report.md')
        with open(summary_file, 'w') as f:
            f.write(summary_report)

        results['summary_report'] = summary_file

        # Log results
        logger.info(
            f"Processed {len(results['processed_files'])} files in {results['processing_time']:.2f} seconds: "
            f"{results['success_count']} success, "
            f"{results['warning_count']} warning, "
            f"{results['error_count']} error"
        )
        logger.info(f"Directory processing complete. Status: {results['status'].name}")
        logger.info(f"Summary report: {summary_file}")

        # Calculate and log performance metrics
        if results['processing_time'] > 0:
            files_per_second = len(results['processed_files']) / results['processing_time']
            logger.info(f"Processing rate: {files_per_second:.2f} files/second")

            if self.adaptive_workers:
                # For adaptive worker pool, report average workers used
                avg_workers = results.get('avg_workers', self.max_workers)
                logger.info(f"Average worker count: {avg_workers:.1f}")
                logger.info(
                    f"Parallel efficiency: {files_per_second / avg_workers:.2f} files/worker/second")
            else:
                # For fixed worker pool, use max_workers
                logger.info(
                    f"Parallel efficiency: {files_per_second / self.max_workers:.2f} files/worker/second")

        return results

    def _process_with_fixed_workers(
        self,
        image_files: List[str],
        doc_type: DocumentType,
        lossless_fallback: bool,
        bnf_compliant: bool,
        compression_ratio_tolerance: float,
        include_bnf_markers: bool,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process files using a fixed worker pool.

        Args:
            image_files: List of image files to process
            doc_type: Document type for compression
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers
            metadata: Additional metadata to include in output files

        Returns:
            Dictionary with processing results
        """
        # Initialize results
        results = {
            'status': WorkflowStatus.SUCCESS,
            'processed_files': [],
            'success_count': 0,
            'warning_count': 0,
            'error_count': 0,
            'corrupted_count': 0,
            'processing_time': 0
        }

        # Create a partial function with the fixed parameters
        worker_func = partial(
            standalone_process_file_worker,
            output_dir=self.config.output_dir,
            report_dir=self.config.report_dir,
            doc_type=doc_type,
            quality_threshold=self.config.quality_threshold,
            num_resolutions=self.config.num_resolutions,
            progression_order=self.config.progression_order,
            compression_mode=self.config.compression_mode,
            lossless_fallback=lossless_fallback,
            bnf_compliant=bnf_compliant,
            compression_ratio_tolerance=compression_ratio_tolerance,
            include_bnf_markers=include_bnf_markers,
            metadata=metadata
        )

        # Process in parallel using a process pool with fixed worker count
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(worker_func, file): file for file in image_files
            }

            # Process results as they complete
            for i, future in enumerate(as_completed(future_to_file)):
                file_result = future.result()
                results['processed_files'].append(file_result)

                if file_result['status'] == WorkflowStatus.SUCCESS.name:
                    results['success_count'] += 1
                elif file_result['status'] == WorkflowStatus.WARNING.name:
                    results['warning_count'] += 1
                    if results['status'] == WorkflowStatus.SUCCESS:
                        results['status'] = WorkflowStatus.WARNING
                elif file_result['status'] == WorkflowStatus.FAILURE.name:
                    results['error_count'] += 1
                    results['status'] = WorkflowStatus.FAILURE
                elif file_result['status'] == WorkflowStatus.SKIPPED.name:
                    results['corrupted_count'] += 1

                # Update progress
                progress = ((i + 1) / self.total_files) * 100
                logger.info(f"Progress: {progress:.1f}% ({i + 1}/{self.total_files})")

                # Calculate and log partial results
                if (i + 1) % 10 == 0 or (i + 1) == self.total_files:
                    elapsed = time.time() - self.start_time
                    files_per_second = (i + 1) / elapsed if elapsed > 0 else 0

                    logger.info(
                        f"Processed {i + 1} files in {elapsed:.2f} seconds "
                        f"({files_per_second:.2f} files/second)"
                    )

        # Calculate total processing time
        results['processing_time'] = time.time() - self.start_time
        return results

    def _process_with_adaptive_workers(
        self,
        image_files: List[str],
        doc_type: DocumentType,
        lossless_fallback: bool,
        bnf_compliant: bool,
        compression_ratio_tolerance: float,
        include_bnf_markers: bool,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process files using an adaptive worker pool.

        Args:
            image_files: List of image files to process
            doc_type: Document type for compression
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers
            metadata: Additional metadata to include in output files

        Returns:
            Dictionary with processing results
        """
        # Initialize results
        results = {
            'status': WorkflowStatus.SUCCESS,
            'processed_files': [],
            'success_count': 0,
            'warning_count': 0,
            'error_count': 0,
            'corrupted_count': 0,
            'processing_time': 0,
            'worker_stats': []
        }

        # Create a partial function with the fixed parameters
        # This makes our worker function much simpler and avoids any state from this class
        worker_func = partial(
            standalone_process_file_worker,
            output_dir=self.config.output_dir,
            report_dir=self.config.report_dir,
            doc_type=doc_type,
            quality_threshold=self.config.quality_threshold,
            num_resolutions=self.config.num_resolutions,
            progression_order=self.config.progression_order,
            compression_mode=self.config.compression_mode,
            lossless_fallback=lossless_fallback,
            bnf_compliant=bnf_compliant,
            compression_ratio_tolerance=compression_ratio_tolerance,
            include_bnf_markers=include_bnf_markers,
            metadata=metadata
        )

        # Start the resource monitor
        self.resource_monitor.start()

        try:
            # Create a list to store worker count samples
            worker_count_samples = []
            files_to_process = list(image_files)  # Make a copy so we can modify it
            processed_count = 0

            # Process files in batches until all are done
            while files_to_process:
                # Get current recommended worker count
                current_workers = self.resource_monitor.get_recommended_workers()
                worker_count_samples.append(current_workers)

                # Determine batch size - how many files to process in this iteration
                batch_size = min(current_workers, len(files_to_process))
                if batch_size < 1:
                    batch_size = 1

                # Get a batch of files to process
                batch_files = files_to_process[:batch_size]
                files_to_process = files_to_process[batch_size:]

                logger.info(
                    f"Processing batch of {len(batch_files)} files with {batch_size} workers")

                # Process this batch using a new ProcessPoolExecutor
                # This avoids any issues with shared state
                with ProcessPoolExecutor(max_workers=batch_size) as executor:
                    futures = []
                    for file_path in batch_files:
                        # Submit the standalone worker function instead of a method on this class
                        future = executor.submit(worker_func, file_path)
                        futures.append(future)

                    # Process results as they complete
                    for future in as_completed(futures):
                        try:
                            file_result = future.result()
                            results['processed_files'].append(file_result)

                            # Update counters based on status
                            if file_result['status'] == WorkflowStatus.SUCCESS.name:
                                results['success_count'] += 1
                            elif file_result['status'] == WorkflowStatus.WARNING.name:
                                results['warning_count'] += 1
                                if results['status'] == WorkflowStatus.SUCCESS:
                                    results['status'] = WorkflowStatus.WARNING
                            elif file_result['status'] == WorkflowStatus.FAILURE.name:
                                results['error_count'] += 1
                                results['status'] = WorkflowStatus.FAILURE
                            elif file_result['status'] == WorkflowStatus.SKIPPED.name:
                                results['corrupted_count'] += 1

                            # Update progress tracking with time estimation
                            processed_count += 1
                            progress = (processed_count / self.total_files) * 100
                            current_time = time.time()
                            elapsed_time = current_time - self.start_time
                            
                            if processed_count > 0:
                                avg_time_per_file = elapsed_time / processed_count
                                remaining_files = self.total_files - processed_count
                                estimated_remaining_time = avg_time_per_file * remaining_files
                                
                                # Format time nicely
                                if estimated_remaining_time > 3600:
                                    time_str = f"{estimated_remaining_time/3600:.1f}h"
                                elif estimated_remaining_time > 60:
                                    time_str = f"{estimated_remaining_time/60:.1f}m"
                                else:
                                    time_str = f"{estimated_remaining_time:.0f}s"
                                    
                                logger.info(
                                    f"Progress: {progress:.1f}% ({processed_count}/{self.total_files}) - Est. remaining: {time_str}")
                            else:
                                logger.info(
                                    f"Progress: {progress:.1f}% ({processed_count}/{self.total_files})")
                            
                            # Force garbage collection to optimize memory usage
                            gc.collect()

                            # Log status periodically
                            if processed_count % 10 == 0 or processed_count == self.total_files:
                                elapsed = time.time() - self.start_time
                                files_per_second = processed_count / elapsed if elapsed > 0 else 0

                                logger.info(
                                    f"Processed {processed_count} files in {elapsed:.2f} seconds "
                                    f"({files_per_second:.2f} files/second), "
                                    f"current workers: {current_workers}"
                                )
                        except Exception as e:
                            logger.error(f"Error processing file: {str(e)}")
                            results['error_count'] += 1
                            if results['status'] == WorkflowStatus.SUCCESS:
                                results['status'] = WorkflowStatus.FAILURE

                # Sleep briefly between batches to allow resource monitor to update
                if files_to_process:
                    time.sleep(0.5)

            # Calculate average worker count
            if worker_count_samples:
                avg_workers = sum(worker_count_samples) / len(worker_count_samples)
            else:
                avg_workers = self.max_workers

            results['avg_workers'] = avg_workers
            results['worker_stats'] = worker_count_samples

        finally:
            # Stop the resource monitor
            if self.resource_monitor:
                self.resource_monitor.stop()

        # Calculate total processing time
        results['processing_time'] = time.time() - self.start_time
        return results
