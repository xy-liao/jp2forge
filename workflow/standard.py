"""
Standard sequential workflow for JPEG2000 processing.

This module provides a sequential implementation of the JPEG2000 workflow.
"""

import os
import gc
import time
import logging
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from core.types import (
    WorkflowStatus,
    DocumentType,
    CompressionMode,
    ProcessingResult,
    WorkflowConfig,
    BnFCompressionRatio
)
from core.metadata.base_handler import MetadataHandler
from core.metadata.bnf_handler import BnFMetadataHandler
from utils.image import (
    validate_image, get_output_path, find_image_files,
    is_multipage_tiff, extract_tiff_page, get_multipage_output_paths
)
from utils.profiling import profile, profile_block, mark_event, save_report
from workflow.base import BaseWorkflow
from workflow.utils import format_file_size, _calculate_file_sizes, _resolve_parameters

logger = logging.getLogger(__name__)


class StandardWorkflow(BaseWorkflow):
    """Sequential implementation of the JPEG2000 workflow."""

    def __init__(self, config: WorkflowConfig):
        """Initialize the workflow with configuration.

        Args:
            config: Workflow configuration
        """
        super().__init__(config)

        # Initialize performance profiling for the workflow
        self.enable_profiling = config.enable_profiling if hasattr(
            config, 'enable_profiling') else False
        if self.enable_profiling:
            from utils.profiling import get_profiler
            get_profiler(output_dir=config.report_dir)
            logger.info("Performance profiling enabled for StandardWorkflow")

        # Create temporary directory for extracted TIFF pages
        self.temp_dir = tempfile.mkdtemp(prefix="jp2forge_")

    def _setup_bnf_metadata(self, metadata, input_file, page_num=None):
        """Setup BnF metadata with default values.
        
        Args:
            metadata: Original metadata dictionary
            input_file: Path to input file
            page_num: Page number for multipage documents (optional)
            
        Returns:
            Dictionary with BnF metadata setup
        """
        metadata_dict = {}
        if metadata:
            metadata_dict.update(metadata)

        # Generate document ID if not provided
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        if page_num is not None:
            default_id = f"NUM_{base_name}_p{page_num}"
        else:
            default_id = f"NUM_{base_name}"
            
        if 'dcterms:isPartOf' not in metadata_dict:
            metadata_dict['dcterms:isPartOf'] = default_id

        # Default BnF provenance if not specified
        if 'dcterms:provenance' not in metadata_dict:
            metadata_dict['dcterms:provenance'] = "Bibliothèque nationale de France"
            
        return metadata_dict

    def _setup_bnf_handler(self):
        """Setup BnF metadata handler if needed.
        
        Returns:
            BnF metadata handler instance
        """
        if not isinstance(self.metadata_handler, BnFMetadataHandler):
            base_handler = MetadataHandler()
            return BnFMetadataHandler(base_handler=base_handler, debug=True)
        else:
            return self.metadata_handler

    def _log_compression_stats(self, input_file, original_size, converted_size, compression_ratio, page_num=None):
        """Log compression statistics for profiling.
        
        Args:
            input_file: Path to input file
            original_size: Original file size in bytes
            converted_size: Converted file size in bytes
            compression_ratio: Compression ratio
            page_num: Page number for multipage documents (optional)
        """
        if self.enable_profiling:
            if page_num is not None:
                file_identifier = f"{os.path.basename(input_file)}_page_{page_num}"
            else:
                file_identifier = os.path.basename(input_file)
                
            mark_event("compression_stats", {
                "input_file": file_identifier,
                "original_size_mb": original_size / (1024 * 1024),
                "converted_size_mb": converted_size / (1024 * 1024),
                "compression_ratio": compression_ratio
            })

    def _handle_metadata_error(self, e, input_file, output_file, metadata_type="standard"):
        """Handle metadata writing errors consistently.
        
        Args:
            e: Exception that occurred
            input_file: Path to input file
            output_file: Path to output file
            metadata_type: Type of metadata for logging
            
        Returns:
            ProcessingResult with warning status
        """
        mark_event("metadata_error", {"error": str(e), "type": f"{metadata_type}_metadata"})
        logger.error(f"Error writing {metadata_type} metadata: {str(e)}")
        return ProcessingResult(
            status=WorkflowStatus.WARNING,
            input_file=input_file,
            output_file=output_file,
            error=f"Converted successfully but metadata failed: {str(e)}"
        )

    def _update_result_status(self, results, result):
        """Update result counters based on processing status.
        
        Args:
            results: Results dictionary to update
            result: ProcessingResult object
        """
        if result.status == WorkflowStatus.SUCCESS:
            results['success_count'] += 1
        elif result.status == WorkflowStatus.WARNING:
            results['warning_count'] += 1
            if results['status'] == WorkflowStatus.SUCCESS:
                results['status'] = WorkflowStatus.WARNING
        elif result.status == WorkflowStatus.FAILURE:
            results['error_count'] += 1
            results['status'] = WorkflowStatus.FAILURE
        elif result.status == WorkflowStatus.SKIPPED:
            results['corrupted_count'] += 1

    def _log_progress_with_estimation(self, processed_count, total_files, start_time):
        """Log processing progress with time estimation.
        
        Args:
            processed_count: Number of files processed so far
            total_files: Total number of files to process
            start_time: Processing start time
        """
        progress = (processed_count / total_files) * 100
        current_time = time.time()
        elapsed_time = current_time - start_time
        
        if processed_count > 0:
            avg_time_per_file = elapsed_time / processed_count
            remaining_files = total_files - processed_count
            estimated_remaining_time = avg_time_per_file * remaining_files
            
            # Format time nicely
            if estimated_remaining_time > 3600:
                time_str = f"{estimated_remaining_time/3600:.1f}h"
            elif estimated_remaining_time > 60:
                time_str = f"{estimated_remaining_time/60:.1f}m"
            else:
                time_str = f"{estimated_remaining_time:.0f}s"
                
            logger.info(
                f"Progress: {progress:.1f}% ({processed_count}/{total_files}) - Est. remaining: {time_str}")
        else:
            logger.info(
                f"Progress: {progress:.1f}% ({processed_count}/{total_files})")

    def __del__(self):
        """Clean up temporary files when workflow is destroyed."""
        self._cleanup_temp_files()

    def _cleanup_temp_files(self):
        """Remove temporary files created for multi-page TIFF processing."""
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")

    @profile("process_file_implementation")
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
        # Check if input is a multi-page TIFF
        is_multipage, page_count = is_multipage_tiff(input_file)

        if is_multipage:
            # Handle multi-page TIFF
            return self._process_multipage_tiff(
                input_file=input_file,
                page_count=page_count,
                doc_type=doc_type,
                lossless_fallback=lossless_fallback,
                bnf_compliant=bnf_compliant,
                compression_ratio_tolerance=compression_ratio_tolerance,
                include_bnf_markers=include_bnf_markers,
                metadata=metadata
            )

        # Original code for single page images
        try:
            # Step 1: Convert to JPEG2000
            with profile_block("conversion_to_jp2"):
                logger.info("Step 1: Converting to JPEG2000")
                output_file = get_output_path(input_file, self.config.output_dir, ".jp2")

                processing_start = time.time()

                # Process according to compression mode
                compression_mode = self.config.compression_mode
                success = self.compressor.convert_to_jp2(
                    input_file,
                    output_file,
                    doc_type,
                    compression_mode,
                    lossless_fallback,
                    bnf_compliant,
                    compression_ratio_tolerance,
                    include_bnf_markers
                )

                processing_time = time.time() - processing_start
                logger.info(f"Conversion completed in {processing_time:.2f} seconds")

                if not success:
                    mark_event("conversion_failed", {"input_file": input_file})
                    return ProcessingResult(
                        status=WorkflowStatus.FAILURE,
                        input_file=input_file,
                        error="Conversion failed"
                    )

            # Step 2: Analyze pixel loss (only in supervised mode)
            report_file = None
            analysis_results = None

            if compression_mode == CompressionMode.SUPERVISED:
                with profile_block("pixel_loss_analysis"):
                    logger.info("Step 2: Analyzing pixel loss")
                    analysis_start = time.time()

                    analysis_result = self.analyzer.analyze_pixel_loss(
                        input_file,
                        output_file,
                        save_report=False  # Changed from True to False to avoid generating individual analysis files
                    )

                    analysis_time = time.time() - analysis_start
                    logger.info(f"Analysis completed in {analysis_time:.2f} seconds")

                    # Check if quality checks failed but we're still returning success
                    if not analysis_result.quality_passed:
                        logger.warning(f"Quality checks failed for {input_file}")
                        mark_event("quality_check_failed", {
                            "input_file": input_file,
                            "psnr": analysis_result.psnr,
                            "ssim": analysis_result.ssim,
                            "mse": analysis_result.mse
                        })
                        # We still return success but with metrics for user review
                        status = WorkflowStatus.WARNING
                        metrics = {
                            "psnr": analysis_result.psnr,
                            "ssim": analysis_result.ssim,
                            "mse": analysis_result.mse,
                            "quality_passed": analysis_result.quality_passed
                        }
                    else:
                        status = WorkflowStatus.SUCCESS
                        metrics = {
                            "psnr": analysis_result.psnr,
                            "ssim": analysis_result.ssim,
                            "mse": analysis_result.mse,
                            "quality_passed": analysis_result.quality_passed
                        }
            else:
                # For non-supervised modes, we don't do analysis
                status = WorkflowStatus.SUCCESS
                metrics = None

            # Step 3: Add metadata
            with profile_block("add_metadata"):
                logger.info("Step 3: Adding metadata")
                # Pass compression parameters to metadata handler
                compression_mode_str = self.config.compression_mode.value

                # For BnF mode, use BnF compliant metadata
                if bnf_compliant or compression_mode == CompressionMode.BNF_COMPLIANT:
                    try:
                        bnf_handler = self._setup_bnf_handler()
                        metadata_dict = self._setup_bnf_metadata(metadata, input_file)
                        
                        self.metadata_handler.write_metadata(
                            output_file,
                            metadata_dict,
                            compression_mode_str,
                            self.config.num_resolutions,
                            self.config.progression_order,
                            True  # bnf_compliant=True
                        )
                    except Exception as e:
                        return self._handle_metadata_error(e, input_file, output_file, "bnf")
                else:
                    # Standard metadata
                    try:
                        self.metadata_handler.write_metadata(
                            output_file,
                            metadata,
                            compression_mode_str,
                            self.config.num_resolutions,
                            self.config.progression_order
                        )
                    except Exception as e:
                        return self._handle_metadata_error(e, input_file, output_file, "standard")

            # Force garbage collection
            with profile_block("cleanup"):
                gc.collect()

            # Calculate file sizes and log compression stats
            file_sizes = None
            try:
                # Create a dummy result object for _calculate_file_sizes
                class DummyResult:
                    def __init__(self, output_file):
                        self.output_file = output_file
                        self.file_sizes = None
                
                dummy_result = DummyResult(output_file)
                file_sizes = _calculate_file_sizes(dummy_result, input_file)
                
                # Log compression stats for profiling
                if file_sizes and self.enable_profiling:
                    original_size = file_sizes.get("original_size", 0)
                    converted_size = file_sizes.get("converted_size", 0)
                    compression_ratio = original_size / converted_size if converted_size > 0 else 0
                    self._log_compression_stats(input_file, original_size, converted_size, compression_ratio)
            except Exception as e:
                logger.warning(f"Error calculating file sizes: {str(e)}")

            logger.info(f"Successfully processed {input_file}")
            self.processed_files_count += 1

            return ProcessingResult(
                status=status,
                input_file=input_file,
                output_file=output_file,
                report_file=report_file,
                metrics=metrics,
                file_sizes=file_sizes
            )

        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            mark_event("processing_error", {"input_file": input_file, "error": str(e)})
            return ProcessingResult(
                status=WorkflowStatus.FAILURE,
                input_file=input_file,
                error=str(e)
            )

    def _process_multipage_tiff(
        self,
        input_file: str,
        page_count: int,
        doc_type: DocumentType,
        lossless_fallback: bool,
        bnf_compliant: bool,
        compression_ratio_tolerance: float,
        include_bnf_markers: bool,
        metadata: Dict[str, Any]
    ) -> ProcessingResult:
        """
        Process a multi-page TIFF file by extracting and converting each page.

        Args:
            input_file: Path to input file
            page_count: Number of pages in the TIFF file
            doc_type: Document type for compression
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers
            metadata: Additional metadata to include in output file

        Returns:
            ProcessingResult: Result of processing, combining results for all pages
        """
        logger.info(f"Processing multi-page TIFF: {input_file} with {page_count} pages")

        # Generate output paths for all pages
        output_paths = get_multipage_output_paths(
            input_file,
            self.config.output_dir,
            ".jp2",
            page_count
        )

        # If the "skip_existing" flag is set, check if output files exist and skip them
        if hasattr(self.config, 'skip_existing') and self.config.skip_existing:
            existing_files = [p for p in output_paths if os.path.exists(p)]
            if existing_files and len(existing_files) == len(output_paths):
                logger.info(f"Skipping {input_file}: All output files already exist")
                return ProcessingResult(
                    status=WorkflowStatus.SUCCESS,
                    input_file=input_file,
                    output_file=",".join(existing_files),
                    error=None,
                    file_sizes=None,
                    metrics={"skipped": True, "reason": "All output files already exist"}
                )

        # Check if we should overwrite existing files
        overwrite = hasattr(self.config, 'overwrite') and self.config.overwrite
        if not overwrite:
            # Filter out paths that already exist and warn
            for path in output_paths:
                if os.path.exists(path):
                    logger.warning(
                        f"Output file already exists and will not be overwritten: {path}")

        # Track results for all pages
        page_results = []
        overall_status = WorkflowStatus.SUCCESS
        combined_file_sizes = {
            "original_size": 0,
            "converted_size": 0,
            "pages": []
        }

        # Apply chunk size and memory limit settings
        chunk_size = self.config.chunk_size if hasattr(self.config, 'chunk_size') else 1000000
        memory_limit_mb = self.config.memory_limit_mb if hasattr(
            self.config, 'memory_limit_mb') else 4096

        # Check if we need memory-efficient processing
        # Using chunk_size and memory_limit_mb instead of the previously used force_chunking
        use_memory_efficient_processing = (hasattr(self.config, 'chunk_size') and
                                           self.config.chunk_size < 1000000) or \
            (hasattr(self.config, 'memory_limit_mb') and
             self.config.memory_limit_mb < 2048)

        # Process each page
        for page_num in range(page_count):
            logger.info(f"Processing page {page_num+1}/{page_count} from {input_file}")
            output_file = output_paths[page_num]

            # Skip existing files if not overwriting
            if not overwrite and os.path.exists(output_file):
                logger.info(f"Skipping existing output file: {output_file}")
                try:
                    page_original_size = 0  # Unknown since we're skipping
                    page_converted_size = os.path.getsize(output_file)

                    # Add to combined sizes
                    combined_file_sizes["converted_size"] += page_converted_size

                    # Add page-specific info
                    combined_file_sizes["pages"].append({
                        "page": page_num + 1,
                        "original_size": 0,  # Unknown
                        "original_size_human": "N/A",  # Unknown
                        "converted_size": page_converted_size,
                        "converted_size_human": format_file_size(page_converted_size),
                        "compression_ratio": "N/A"  # Unknown
                    })

                    page_results.append({
                        "page": page_num + 1,
                        "status": "SUCCESS",
                        "output_file": output_file,
                        "skipped": True
                    })

                    continue
                except Exception as e:
                    logger.warning(f"Error checking existing file {output_file}: {str(e)}")

            try:
                # Extract the page to a temporary file
                temp_tiff = extract_tiff_page(input_file, page_num, self.temp_dir)

                # Process the extracted page (similar to single page processing)
                with profile_block(f"page{page_num}_conversion"):
                    # Add page number to metadata
                    page_metadata = metadata.copy() if metadata else {}
                    page_metadata["tiff:PageNumber"] = f"{page_num+1}/{page_count}"

                    # Process according to compression mode
                    compression_mode = self.config.compression_mode

                    # Set any additional compressor options specific to this workflow config
                    if hasattr(self.config, 'use_memory_pool') and hasattr(self.compressor, 'use_memory_pool'):
                        self.compressor.use_memory_pool = self.config.use_memory_pool
                    if hasattr(self.config, 'memory_pool_size_mb') and hasattr(self.compressor, 'memory_pool_size_mb'):
                        self.compressor.memory_pool_size_mb = self.config.memory_pool_size_mb

                    # Use custom target compression ratio if specified
                    if hasattr(self.config, 'target_compression_ratio') and self.config.target_compression_ratio:
                        logger.info(
                            f"Using target compression ratio: {self.config.target_compression_ratio}")
                        # Since target_compression_ratio is not a standard parameter for convert_to_jp2,
                        # we'll need to handle this with the specific encoding implementation in the future

                    # Configure memory-efficient processing if needed
                    if use_memory_efficient_processing:
                        logger.info(
                            f"Using memory-efficient processing for page {page_num+1} with chunk_size={chunk_size}, memory_limit_mb={memory_limit_mb}")
                        # We'll need to implement this in the compressor

                    # Convert using all specified parameters
                    success = self.compressor.convert_to_jp2(
                        temp_tiff,
                        output_file,
                        doc_type,
                        compression_mode,
                        lossless_fallback,
                        bnf_compliant,
                        compression_ratio_tolerance,
                        include_bnf_markers
                    )

                    if not success:
                        logger.error(f"Failed to convert page {page_num+1} from {input_file}")
                        overall_status = WorkflowStatus.FAILURE
                        page_results.append({
                            "page": page_num + 1,
                            "status": "FAILURE",
                            "output_file": None,
                            "error": "Conversion failed"
                        })
                        continue

                # Add metadata for this page
                try:
                    # Choose the right metadata handler based on BnF compliance
                    if bnf_compliant or compression_mode == CompressionMode.BNF_COMPLIANT:
                        bnf_handler = self._setup_bnf_handler()
                        page_metadata_dict = self._setup_bnf_metadata(page_metadata, input_file, page_num + 1)
                        
                        self.metadata_handler.write_metadata(
                            output_file,
                            page_metadata_dict,
                            compression_mode.value,
                            self.config.num_resolutions,
                            self.config.progression_order,
                            True  # bnf_compliant=True
                        )
                    else:
                        # Standard metadata
                        self.metadata_handler.write_metadata(
                            output_file,
                            page_metadata,
                            compression_mode.value,
                            self.config.num_resolutions,
                            self.config.progression_order
                        )
                except Exception as e:
                    logger.warning(f"Failed to write metadata for page {page_num+1}: {str(e)}")
                    # Continue processing despite metadata error

                # Run analysis if in supervised mode
                if compression_mode == CompressionMode.SUPERVISED:
                    try:
                        analysis_result = self.analyzer.analyze_pixel_loss(
                            temp_tiff,
                            output_file,
                            save_report=False
                        )

                        # Add quality metrics to page results
                        page_metrics = {
                            "psnr": analysis_result.psnr,
                            "ssim": analysis_result.ssim,
                            "mse": analysis_result.mse,
                            "quality_passed": analysis_result.quality_passed
                        }
                    except Exception as e:
                        logger.warning(f"Error analyzing quality for page {page_num+1}: {str(e)}")
                        page_metrics = None
                else:
                    page_metrics = None

                # Calculate file sizes for this page
                try:
                    page_original_size = os.path.getsize(temp_tiff)
                    page_converted_size = os.path.getsize(output_file)
                    page_ratio = page_original_size / page_converted_size if page_converted_size > 0 else 0

                    # Add to combined sizes
                    combined_file_sizes["original_size"] += page_original_size
                    combined_file_sizes["converted_size"] += page_converted_size

                    # Add page-specific info
                    combined_file_sizes["pages"].append({
                        "page": page_num + 1,
                        "original_size": page_original_size,
                        "original_size_human": format_file_size(page_original_size),
                        "converted_size": page_converted_size,
                        "converted_size_human": format_file_size(page_converted_size),
                        "compression_ratio": f"{page_ratio:.2f}:1"
                    })

                    # Log compression stats for profiling
                    self._log_compression_stats(input_file, page_original_size, page_converted_size, page_ratio, page_num + 1)

                except Exception as e:
                    logger.warning(f"Error calculating file sizes for page {page_num+1}: {str(e)}")

                # Store page result with any metrics
                page_results.append({
                    "page": page_num + 1,
                    "status": "SUCCESS",
                    "output_file": output_file,
                    "metrics": page_metrics
                })

                logger.info(
                    f"Successfully processed page {page_num+1}/{page_count} from {input_file}")

            except Exception as e:
                logger.error(f"Error processing page {page_num+1} from {input_file}: {str(e)}")
                overall_status = WorkflowStatus.FAILURE
                page_results.append({
                    "page": page_num + 1,
                    "status": "FAILURE",
                    "error": str(e)
                })

            # Force garbage collection after each page
            gc.collect()

            # Don't clean up temporary files if keep_temp is enabled
            if hasattr(self.config, 'keep_temp') and self.config.keep_temp:
                logger.info(f"Keeping temporary file for page {page_num+1}: {temp_tiff}")
            else:
                try:
                    if os.path.exists(temp_tiff):
                        os.remove(temp_tiff)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_tiff}: {str(e)}")

        # Format combined file sizes
        if combined_file_sizes["original_size"] > 0 and combined_file_sizes["converted_size"] > 0:
            total_ratio = combined_file_sizes["original_size"] / \
                combined_file_sizes["converted_size"]
            combined_file_sizes["original_size_human"] = format_file_size(
                combined_file_sizes["original_size"])
            combined_file_sizes["converted_size_human"] = format_file_size(
                combined_file_sizes["converted_size"])
            combined_file_sizes["compression_ratio"] = f"{total_ratio:.2f}:1"

        # Check if all pages were processed successfully
        success_count = sum(1 for r in page_results if r["status"] == "SUCCESS")

        if success_count == 0:
            overall_status = WorkflowStatus.FAILURE
            error_message = "Failed to process any pages from multi-page TIFF"
        elif success_count < page_count:
            overall_status = WorkflowStatus.WARNING
            error_message = f"Processed {success_count} of {page_count} pages successfully"
        else:
            overall_status = WorkflowStatus.SUCCESS
            error_message = None

        logger.info(
            f"Completed processing multi-page TIFF: {input_file}, status: {overall_status.name}")

        # Return combined result
        return ProcessingResult(
            status=overall_status,
            input_file=input_file,
            output_file=",".join([r["output_file"] for r in page_results if r.get("output_file")]),
            error=error_message,
            file_sizes=combined_file_sizes,
            metrics={"multipage_results": page_results}
        )

    @profile("process_directory")
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
        """Process all files in a directory sequentially.

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
        doc_type, recursive, lossless_fallback, bnf_compliant, compression_ratio_tolerance, include_bnf_markers = _resolve_parameters(
            self.config, doc_type, recursive, lossless_fallback, bnf_compliant, 
            compression_ratio_tolerance, include_bnf_markers
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
            'processing_time': 0
        }

        # Initialize tracking variables
        self.processed_files_count = 0
        self.start_time = time.time()

        # Find all image files to process
        with profile_block("find_image_files"):
            image_files = find_image_files(input_dir, recursive)

        self.total_files = len(image_files)
        logger.info(f"Found {self.total_files} image files to process")

        if self.enable_profiling:
            mark_event("batch_processing_start", {
                "total_files": self.total_files,
                "input_dir": input_dir,
                "recursive": recursive
            })

        # Process files sequentially
        for i, input_file in enumerate(image_files):
            result = self.process_file(
                input_file=input_file,
                doc_type=doc_type,
                lossless_fallback=lossless_fallback,
                bnf_compliant=bnf_compliant,
                compression_ratio_tolerance=compression_ratio_tolerance,
                include_bnf_markers=include_bnf_markers,
                metadata=metadata
            )

            # Convert ProcessingResult to dictionary for report
            file_result = {
                'input_file': result.input_file,
                'status': result.status.name,
                'output_file': result.output_file,
                'report_file': result.report_file,
                'error': result.error
            }

            # Add file sizes if available
            if result.file_sizes:
                file_result['file_sizes'] = result.file_sizes

            results['processed_files'].append(file_result)

            # Update status counters
            self._update_result_status(results, result)

            # Update progress with time estimation
            self._log_progress_with_estimation(len(results['processed_files']), self.total_files, self.start_time)
            
            # Force garbage collection to optimize memory usage
            gc.collect()

            # If there are errors, we still continue processing other files

            # Log batch progress every 5% or 10 files, whichever comes first
            should_log_progress = (i % 10 == 9) or (i > 0 and int(
                progress / 5) > int(((i - 1) / self.total_files * 100) / 5))
            if should_log_progress and self.enable_profiling:
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                files_per_second = (i + 1) / elapsed_time if elapsed_time > 0 else 0
                estimated_remaining = (self.total_files - (i + 1)) / \
                    files_per_second if files_per_second > 0 else 0

                mark_event("batch_progress", {
                    "processed": i + 1,
                    "total": self.total_files,
                    "percent_complete": progress,
                    "files_per_second": files_per_second,
                    "estimated_remaining_seconds": estimated_remaining
                })

        # Calculate total processing time
        results['processing_time'] = time.time() - self.start_time

        # Generate summary report
        with profile_block("generate_summary_report"):
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
        logger.info(
            f"Processing rate: {len(results['processed_files']) / results['processing_time']:.2f} files/second")

        if self.enable_profiling:
            mark_event("batch_processing_complete", {
                "total_files": self.total_files,
                "success_count": results['success_count'],
                "warning_count": results['warning_count'],
                "error_count": results['error_count'],
                "corrupted_count": results['corrupted_count'],
                "total_duration": results['processing_time'],
                "files_per_second": len(results['processed_files']) / results['processing_time']
                if results['processing_time'] > 0 else 0
            })

            # Save performance profile report
            profile_report_path = save_report(
                f"profile_report_standard_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            logger.info(f"Saved performance profile report to {profile_report_path}")

        return results
