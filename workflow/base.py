"""
Base workflow module for JPEG2000 processing.

This module provides the abstract base class for JPEG2000 workflows,
defining the common interface and functionality.
"""

import os
import logging
import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from core.types import (
    WorkflowStatus, 
    DocumentType, 
    CompressionMode, 
    ProcessingMode,
    ProcessingResult,
    WorkflowConfig,
    BnFCompressionRatio
)
from core.compressor import JPEG2000Compressor
from core.analyzer import ImageAnalyzer
from core.metadata import get_metadata_handler
from utils.image import validate_image, get_output_path, find_image_files

logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Abstract base class for JPEG2000 workflows."""
    
    def __init__(self, config: WorkflowConfig):
        """Initialize the workflow.
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        
        # Create output directories
        os.makedirs(self.config.output_dir, exist_ok=True)
        os.makedirs(self.config.report_dir, exist_ok=True)
        
        # Initialize components
        self.compressor = JPEG2000Compressor(
            num_resolutions=config.num_resolutions,
            progression_order=config.progression_order,
            chunk_size=config.chunk_size,
            memory_limit_mb=config.memory_limit_mb
        )
        self.analyzer = ImageAnalyzer(
            psnr_threshold=config.quality_threshold,
            ssim_threshold=0.95,
            mse_threshold=50.0,
            report_dir=config.report_dir
        )
        
        # Initialize metadata handler based on BnF compliance
        self.metadata_handler = get_metadata_handler(
            config.bnf_compliant if hasattr(config, 'bnf_compliant') else False
        )
        
        # Statistics and tracking
        self.processed_files_count = 0
        self.total_files = 0
        self.start_time = None
        
        # Log initialization
        logger.info(f"Initialized workflow with output directory: {config.output_dir}")
        logger.info(f"Quality threshold (PSNR): {config.quality_threshold}")
        logger.info(f"Number of resolution levels: {config.num_resolutions}")
        logger.info(f"Progression order: {config.progression_order}")
        logger.info(f"Compression mode: {config.compression_mode.value}")
        
        # Handle processing_mode which might be a string or an enum
        if isinstance(config.processing_mode, str):
            logger.info(f"Processing mode: {config.processing_mode.upper()}")
        else:
            logger.info(f"Processing mode: {config.processing_mode.name}")
        
        if hasattr(config, 'bnf_compliant') and config.bnf_compliant:
            logger.info("BnF compliant mode enabled")
            if hasattr(config, 'compression_ratio_tolerance'):
                logger.info(f"Compression ratio tolerance: {config.compression_ratio_tolerance * 100:.1f}%")
    
    def process_file(
        self,
        input_file: str,
        doc_type: Optional[DocumentType] = None,
        lossless_fallback: Optional[bool] = None,
        bnf_compliant: Optional[bool] = None,
        compression_ratio_tolerance: Optional[float] = None,
        include_bnf_markers: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """Process a single file through the workflow.
        
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
        # Use configuration defaults if not specified
        doc_type = doc_type or self.config.document_type
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
        
        try:
            # Validate input file
            is_valid, error_msg = validate_image(input_file)
            if not is_valid:
                logger.error(f"Invalid image {input_file}: {error_msg}")
                return ProcessingResult(
                    status=WorkflowStatus.FAILURE,
                    input_file=input_file,
                    error=error_msg
                )
            
            logger.info(f"Processing file: {input_file}")
            logger.info(f"Document type: {doc_type}")
            
            # Implementation of actual processing handled by subclasses
            return self._process_file_implementation(
                input_file,
                doc_type,
                lossless_fallback,
                bnf_compliant,
                compression_ratio_tolerance,
                include_bnf_markers,
                metadata
            )
            
        except Exception as e:
            logger.error(f"Error processing {input_file}: {str(e)}")
            return ProcessingResult(
                status=WorkflowStatus.FAILURE,
                input_file=input_file,
                error=str(e)
            )
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        """Process all files in a directory.
        
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
        # Validate output directory before processing
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
        
        # Implementation provided by subclasses
        pass
    
    def _format_file_size(self, size_in_bytes: int) -> str:
        """Format file size in human-readable format.
        
        Args:
            size_in_bytes: File size in bytes
            
        Returns:
            str: Human-readable file size
        """
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(size_in_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.2f} {units[unit_index]}"
    
    def _generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report of the processing results.
        
        Args:
            results: Dictionary containing processing results
            
        Returns:
            String containing the summary report
        """
        report = []
        report.append("# JPEG2000 Conversion Summary Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        report.append("## Overall Statistics")
        report.append("-----------------")
        report.append(f"Total Files: {len(results.get('processed_files', []))}")
        report.append(f"Successful: {results.get('success_count', 0)}")
        report.append(f"Warnings: {results.get('warning_count', 0)}")
        report.append(f"Errors: {results.get('error_count', 0)}")
        report.append(f"Corrupted: {results.get('corrupted_count', 0)}")
        
        # Add multi-page statistic if we processed any multi-page TIFFs
        multipage_files = 0
        total_pages = 0
        for file_result in results.get('processed_files', []):
            if file_result.get('file_sizes') and 'pages' in file_result.get('file_sizes', {}):
                multipage_files += 1
                total_pages += len(file_result['file_sizes']['pages'])
                
        if multipage_files > 0:
            report.append(f"Multi-page TIFFs: {multipage_files}")
            report.append(f"Total Pages Processed: {total_pages}")
            
        report.append(f"Overall Status: {results['status'].name}")
        
        if 'processing_time' in results:
            report.append(f"Total Processing Time: {results['processing_time']:.2f} seconds")
            if results['processing_time'] > 0 and len(results.get('processed_files', [])) > 0:
                report.append(f"Average Processing Rate: {len(results['processed_files']) / results['processing_time']:.2f} files/second\n")
        
        # Add performance metrics if available
        if self.config.processing_mode == ProcessingMode.PARALLEL and 'max_workers' in results:
            report.append("## Performance Metrics")
            report.append("-----------------")
            report.append(f"Worker Processes: {results['max_workers']}")
            if 'processing_time' in results and results['processing_time'] > 0 and len(results.get('processed_files', [])) > 0:
                report.append(f"Parallel Efficiency: {len(results['processed_files']) / (results['max_workers'] * results['processing_time']):.2f} files/worker/second\n")
        
        report.append("## Configuration")
        report.append("-----------------")
        report.append(f"Document Type: {self.config.document_type.name}")
        report.append(f"Compression Mode: {self.config.compression_mode.value}")
        
        # Handle processing_mode which might be a string or an enum
        if isinstance(self.config.processing_mode, str):
            report.append(f"Processing Mode: {self.config.processing_mode.upper()}")
        else:
            report.append(f"Processing Mode: {self.config.processing_mode.name}")
        
        report.append(f"Quality Threshold: {self.config.quality_threshold}")
        report.append(f"Number of Resolution Levels: {self.config.num_resolutions}")
        report.append(f"Progression Order: {self.config.progression_order}")
        
        # Add BnF compliance info if applicable
        if hasattr(self.config, 'bnf_compliant') and self.config.bnf_compliant:
            report.append(f"BnF Compliant: Yes")
            if hasattr(self.config, 'compression_ratio_tolerance'):
                report.append(f"Compression Ratio Tolerance: {self.config.compression_ratio_tolerance * 100:.1f}%")
        else:
            report.append(f"BnF Compliant: No")
            
        report.append("\n")
        
        report.append("## Detailed Results")
        report.append("----------------")
        
        # Sort files by status for better readability
        processed_files = results.get('processed_files', [])
        if processed_files:
            sorted_files = sorted(
                processed_files, 
                key=lambda x: (
                    # Order: FAILURE, WARNING, SUCCESS
                    0 if x['status'] == WorkflowStatus.FAILURE.name else 
                    1 if x['status'] == WorkflowStatus.WARNING.name else 2,
                    x['input_file']  # Then by filename
                )
            )
            
            for file_result in sorted_files:
                report.append(f"File: {file_result['input_file']}")
                report.append(f"Status: {file_result['status']}")
                if file_result.get('output_file'):
                    report.append(f"Output: {file_result['output_file']}")
                
                # Add file sizes if available
                if file_result.get('file_sizes'):
                    sizes = file_result['file_sizes']
                    report.append(f"Original Size: {sizes.get('original_size_human', 'N/A')}")
                    report.append(f"Converted Size: {sizes.get('converted_size_human', 'N/A')}")
                    report.append(f"Compression Ratio: {sizes.get('compression_ratio', 'N/A')}")
                    
                    # Add multi-page information if available
                    if 'pages' in sizes:
                        report.append(f"Pages: {len(sizes['pages'])}")
                        for page_info in sizes['pages']:
                            report.append(f"  - Page {page_info['page']}: "
                                         f"{page_info['compression_ratio']} ratio, "
                                         f"{page_info['original_size_human']} → "
                                         f"{page_info['converted_size_human']}")
                    
                if file_result.get('report_file'):
                    report.append(f"Report: {file_result['report_file']}")
                
                if file_result.get('error'):
                    report.append(f"Error: {file_result['error']}")
                
                report.append("")
        
        return "\n".join(report)
