"""
Core types for JPEG2000 processing.

This module defines the common types and enumerations used
throughout the JPEG2000 workflow.

Developer Note:
    IMPORTANT NOTATION CONVENTION - Compression ratios in this project use the format N:1
    (e.g., "4:1" or simply "4.0"), while BnF documentation uses 1:N format.
    See docs/NOTATION.md for detailed explanation.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, NamedTuple, Union, List, Tuple, Set


class DocumentType(Enum):
    """Document types for JPEG2000 conversion."""
    PHOTOGRAPH = auto()
    HERITAGE_DOCUMENT = auto()
    COLOR = auto()
    GRAYSCALE = auto()


class WorkflowStatus(Enum):
    """Status codes for workflow operations."""
    SUCCESS = auto()
    WARNING = auto()
    FAILURE = auto()
    SKIPPED = auto()


class ProcessingMode(Enum):
    """Processing modes for the workflow."""
    SEQUENTIAL = auto()
    PARALLEL = auto()


class CompressionMode(Enum):
    """Compression modes for JPEG2000 conversion."""
    LOSSLESS = "lossless"
    LOSSY = "lossy"
    SUPERVISED = "supervised"
    BNF_COMPLIANT = "bnf_compliant"


class BnFCompressionRatio:
    """Compression ratios based on BnF specifications for different document types.

    These compression ratios are implemented according to the BnF (Bibliothèque nationale
    de France) specifications in their "Référentiel de format de fichier image v2" (2015).
    This implementation is provided for educational purposes.

    Note on notation: BnF documentation uses the format "1:4", which means "one part compressed
    to four parts original". However, in this code we use the more common image processing
    notation of N:1 (e.g. "4.0" or "4:1"), which means "four parts original to one part
    compressed". The numerical values (4.0, 6.0, 16.0) represent the ratio of original size
    to compressed size.

    See: https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf
    """
    # BnF notation: 1:4, our code uses 4.0 (4:1) to represent the same ratio
    SPECIALIZED = 4.0  # For specialized documents (prints, photographs, etc.)
    # BnF notation: 1:4, our code uses 4.0 (4:1) to represent the same ratio
    EXCEPTIONAL = 4.0  # For exceptional documents (manuscripts with illuminations, etc.)
    # BnF notation: 1:6, our code uses 6.0 (6:1) to represent the same ratio
    PRINTED = 6.0      # For printed documents
    # BnF notation: 1:16, our code uses 16.0 (16:1) to represent the same ratio
    TRANSPARENT = 16.0  # For transparent documents in grayscale

    @staticmethod
    def get_ratio_for_type(doc_type: DocumentType) -> float:
        """Get BnF compression ratio for document type.

        Args:
            doc_type: Document type

        Returns:
            float: Target compression ratio
        """
        if doc_type == DocumentType.PHOTOGRAPH or doc_type == DocumentType.HERITAGE_DOCUMENT:
            return BnFCompressionRatio.SPECIALIZED
        elif doc_type == DocumentType.COLOR:
            return BnFCompressionRatio.PRINTED
        elif doc_type == DocumentType.GRAYSCALE:
            return BnFCompressionRatio.TRANSPARENT
        else:
            return BnFCompressionRatio.PRINTED


class AnalysisResult(NamedTuple):
    """Results from image analysis."""
    psnr: float
    ssim: float
    mse: float
    quality_passed: bool
    error: Optional[str] = None


class ProcessingResult(NamedTuple):
    """Result of processing a single file."""
    status: WorkflowStatus
    input_file: str
    output_file: Optional[str] = None
    report_file: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    file_sizes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class WorkflowConfig:
    """Configuration for the JPEG2000 workflow."""

    def __init__(
        self,
        output_dir: str,
        report_dir: str,
        document_type: DocumentType = DocumentType.PHOTOGRAPH,
        quality_threshold: float = 40.0,
        num_resolutions: int = 10,
        progression_order: str = "RPCL",
        compression_mode: CompressionMode = CompressionMode.SUPERVISED,
        processing_mode: ProcessingMode = ProcessingMode.SEQUENTIAL,
        max_workers: Optional[int] = None,
        memory_limit_mb: int = 4096,
        # New adaptive worker pool parameters
        adaptive_workers: bool = False,
        min_workers: int = 1,
        memory_threshold: float = 0.8,
        cpu_threshold: float = 0.9,
        # Other parameters
        chunk_size: int = 1000000,
        lossless_fallback: bool = True,
        verbose: bool = False,
        recursive: bool = False,
        bnf_compliant: bool = False,
        compression_ratio_tolerance: float = 0.05,
        include_bnf_markers: bool = True,
        # New optimization options
        use_memory_pool: bool = True,
        memory_pool_size_mb: int = 100,
        memory_pool_max_blocks: int = 10,
        enable_profiling: bool = False,
        detailed_memory_tracking: bool = False,
        # Additional CLI parameters
        no_compression: bool = False,
        strict: bool = False,
        no_upscale: bool = False,
        keep_temp: bool = False,
        overwrite: bool = False,
        skip_existing: bool = False,
        collector_batch_size: int = 10,
        collector_threads: int = 1,
        converter_threads: Optional[int] = None,
        target_compression_ratio: Optional[float] = None,
        target_size: Optional[int] = None
    ):
        """Initialize the workflow configuration.

        Args:
            output_dir: Directory for output files
            report_dir: Directory for reports
            document_type: Type of document being processed
            quality_threshold: PSNR threshold for quality control
            num_resolutions: Number of resolution levels
            progression_order: Progression order for JPEG2000
            compression_mode: Compression mode
            processing_mode: Processing mode (sequential or parallel)
            max_workers: Maximum number of worker processes
            memory_limit_mb: Memory limit in MB for adaptive processing
            adaptive_workers: Whether to enable adaptive worker pool scaling
            min_workers: Minimum number of worker processes for adaptive scaling
            memory_threshold: Memory usage threshold (0-1) for adaptive scaling
            cpu_threshold: CPU usage threshold (0-1) for adaptive scaling
            chunk_size: Number of pixels to process at once for large images
            lossless_fallback: Whether to fall back to lossless compression
            verbose: Enable verbose logging
            recursive: Process subdirectories recursively
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers
            use_memory_pool: Whether to use memory pooling for better performance
            memory_pool_size_mb: Size of each memory pool block in MB
            memory_pool_max_blocks: Maximum number of memory pool blocks
            enable_profiling: Enable performance profiling
            detailed_memory_tracking: Enable detailed memory tracking (requires profiling)
            no_compression: Skip compression step (for debugging)
            strict: Enable strict mode for error handling
            no_upscale: Don't upscale images to minimum dimensions
            keep_temp: Keep temporary files
            overwrite: Overwrite existing files
            skip_existing: Skip existing files
            collector_batch_size: Number of files to process in a batch
            collector_threads: Number of threads to use for collection
            converter_threads: Number of threads to use for conversion
            target_compression_ratio: Target compression ratio (e.g., 20 for 20:1)
            target_size: Target size in bytes for compressed images
        """
        self.output_dir = output_dir
        self.report_dir = report_dir
        self.document_type = document_type
        self.quality_threshold = quality_threshold
        self.num_resolutions = num_resolutions
        self.progression_order = progression_order
        self.compression_mode = compression_mode
        self.processing_mode = processing_mode
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        # New adaptive worker pool parameters
        self.adaptive_workers = adaptive_workers
        self.min_workers = min_workers
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        # Other parameters
        self.chunk_size = chunk_size
        self.lossless_fallback = lossless_fallback
        self.verbose = verbose
        self.recursive = recursive
        self.bnf_compliant = bnf_compliant
        self.compression_ratio_tolerance = compression_ratio_tolerance
        self.include_bnf_markers = include_bnf_markers

        # Initialize new optimization options
        self.use_memory_pool = use_memory_pool
        self.memory_pool_size_mb = memory_pool_size_mb
        self.memory_pool_max_blocks = memory_pool_max_blocks
        self.enable_profiling = enable_profiling
        self.detailed_memory_tracking = detailed_memory_tracking

        # Initialize additional CLI parameters
        self.no_compression = no_compression
        self.strict = strict
        self.no_upscale = no_upscale
        self.keep_temp = keep_temp
        self.overwrite = overwrite
        self.skip_existing = skip_existing
        self.collector_batch_size = collector_batch_size
        self.collector_threads = collector_threads
        self.converter_threads = converter_threads
        self.target_compression_ratio = target_compression_ratio
        self.target_size = target_size

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'WorkflowConfig':
        """Create a configuration from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            WorkflowConfig instance
        """
        # Handle enum conversions
        if 'document_type' in config_dict and isinstance(config_dict['document_type'], str):
            config_dict['document_type'] = DocumentType[config_dict['document_type'].upper()]

        if 'compression_mode' in config_dict and isinstance(config_dict['compression_mode'], str):
            config_dict['compression_mode'] = CompressionMode(config_dict['compression_mode'])

        if 'processing_mode' in config_dict and isinstance(config_dict['processing_mode'], str):
            config_dict['processing_mode'] = ProcessingMode[config_dict['processing_mode'].upper()]

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary containing configuration values
        """
        return {
            'output_dir': self.output_dir,
            'report_dir': self.report_dir,
            'document_type': self.document_type.name,
            'quality_threshold': self.quality_threshold,
            'num_resolutions': self.num_resolutions,
            'progression_order': self.progression_order,
            'compression_mode': self.compression_mode.value,
            'processing_mode': self.processing_mode.name,
            'max_workers': self.max_workers,
            'memory_limit_mb': self.memory_limit_mb,
            # Add new adaptive worker pool parameters
            'adaptive_workers': self.adaptive_workers,
            'min_workers': self.min_workers,
            'memory_threshold': self.memory_threshold,
            'cpu_threshold': self.cpu_threshold,
            'chunk_size': self.chunk_size,
            'lossless_fallback': self.lossless_fallback,
            'verbose': self.verbose,
            'recursive': self.recursive,
            'bnf_compliant': self.bnf_compliant,
            'compression_ratio_tolerance': self.compression_ratio_tolerance,
            'include_bnf_markers': self.include_bnf_markers,
            # Add new optimization options
            'use_memory_pool': self.use_memory_pool,
            'memory_pool_size_mb': self.memory_pool_size_mb,
            'memory_pool_max_blocks': self.memory_pool_max_blocks,
            'enable_profiling': self.enable_profiling,
            'detailed_memory_tracking': self.detailed_memory_tracking,
            # Add additional CLI parameters
            'no_compression': self.no_compression,
            'strict': self.strict,
            'no_upscale': self.no_upscale,
            'keep_temp': self.keep_temp,
            'overwrite': self.overwrite,
            'skip_existing': self.skip_existing,
            'collector_batch_size': self.collector_batch_size,
            'collector_threads': self.collector_threads,
            'converter_threads': self.converter_threads,
            'target_compression_ratio': self.target_compression_ratio,
            'target_size': self.target_size,
        }
