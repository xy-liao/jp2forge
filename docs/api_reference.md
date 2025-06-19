# JP2Forge API Reference

This document provides detailed information about JP2Forge's core classes and functions.

## Table of Contents

1. [Core Types](#1-core-types)
2. [JPEG2000Compressor](#2-jpeg2000compressor)
3. [ImageAnalyzer](#3-imageanalyzer)
4. [MetadataHandler](#4-metadatahandler)
5. [Workflow Classes](#5-workflow-classes)
6. [Utility Functions](#6-utility-functions)

## 1. Core Types

### DocumentType

Enumeration of supported document types:

```python
class DocumentType(Enum):
    PHOTOGRAPH = auto()
    HERITAGE_DOCUMENT = auto()
    COLOR = auto()
    GRAYSCALE = auto()
```

### CompressionMode

Enumeration of compression modes:

```python
class CompressionMode(Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"
    SUPERVISED = "supervised"
    BNF_COMPLIANT = "bnf_compliant"
```

### WorkflowConfig

Configuration class for JP2Forge workflows:

```python
class WorkflowConfig:
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
        # ... additional parameters
    ):
```

**Key Parameters:**
- `output_dir`: Directory for converted JP2 files
- `report_dir`: Directory for processing reports
- `document_type`: Type of document being processed
- `quality_threshold`: PSNR threshold for quality control
- `compression_mode`: Compression mode to use
- `bnf_compliant`: Enable BnF compliance mode

### ProcessingResult

Result object for file processing operations:

```python
class ProcessingResult(NamedTuple):
    status: WorkflowStatus
    input_file: str
    output_file: Optional[str] = None
    report_file: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    file_sizes: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### AnalysisResult

Result object for image quality analysis:

```python
class AnalysisResult(NamedTuple):
    psnr: float
    ssim: float
    mse: float
    quality_passed: bool
    error: Optional[str] = None
```

## 2. JPEG2000Compressor

Main class for JPEG2000 compression operations.

### Constructor

```python
def __init__(
    self,
    num_resolutions: int = 10,
    progression_order: str = "RPCL",
    chunk_size: int = 1000000,
    memory_limit_mb: int = 4096
):
```

**Parameters:**
- `num_resolutions`: Number of resolution levels
- `progression_order`: JPEG2000 progression order (RPCL, LRCP, etc.)
- `chunk_size`: Pixels to process at once for large images
- `memory_limit_mb`: Memory limit for adaptive processing

### Methods

#### convert_to_jp2()

```python
def convert_to_jp2(
    self,
    input_file: str,
    output_file: str,
    doc_type: DocumentType,
    compression_mode: CompressionMode = CompressionMode.SUPERVISED,
    lossless_fallback: bool = True,
    bnf_compliant: bool = False,
    compression_ratio_tolerance: float = 0.05,
    include_bnf_markers: bool = True
) -> bool:
```

Convert an image to JPEG2000 format.

**Parameters:**
- `input_file`: Path to input image
- `output_file`: Path for output JP2 file
- `doc_type`: Document type for compression parameters
- `compression_mode`: Compression mode to use
- `lossless_fallback`: Fall back to lossless if quality thresholds not met
- `bnf_compliant`: Use BnF-compliant settings
- `compression_ratio_tolerance`: Tolerance for BnF compression ratios
- `include_bnf_markers`: Include BnF robustness markers

**Returns:**
- `bool`: True if conversion successful

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `RuntimeError`: If conversion fails critically

#### get_recommended_settings()

```python
def get_recommended_settings(
    self,
    input_file: str,
    doc_type: DocumentType
) -> Dict[str, Any]:
```

Get recommended compression settings for an image.

**Parameters:**
- `input_file`: Path to input image
- `doc_type`: Document type

**Returns:**
- `dict`: Recommended settings including compression mode, parameters, and memory requirements

## 3. ImageAnalyzer

Class for analyzing image quality and pixel loss.

### Constructor

```python
def __init__(
    self,
    psnr_threshold: float = 40.0,
    ssim_threshold: float = 0.95,
    mse_threshold: float = 50.0,
    report_dir: Optional[str] = None
):
```

**Parameters:**
- `psnr_threshold`: PSNR threshold for quality control
- `ssim_threshold`: SSIM threshold for quality control
- `mse_threshold`: MSE threshold for quality control
- `report_dir`: Directory for analysis reports

### Methods

#### analyze_pixel_loss()

```python
def analyze_pixel_loss(
    self,
    original_path: str,
    converted_path: str,
    save_report: bool = False
) -> AnalysisResult:
```

Analyze pixel loss between original and converted images.

**Parameters:**
- `original_path`: Path to original image
- `converted_path`: Path to converted image
- `save_report`: Whether to save detailed analysis report

**Returns:**
- `AnalysisResult`: Analysis results with quality metrics

## 4. MetadataHandler

Base class for metadata operations.

### Factory Function

```python
def get_metadata_handler(bnf_compliant: bool = False):
    """Get appropriate metadata handler."""
    if bnf_compliant:
        return BnFMetadataHandler()
    else:
        return MetadataHandler()
```

### BnFMetadataHandler

Specialized handler for BnF-compliant metadata.

#### create_bnf_compliant_metadata()

```python
def create_bnf_compliant_metadata(
    self,
    identifiant: str,
    provenance: str = "Bibliothèque nationale de France",
    ark_identifiant: Optional[str] = None,
    cote: Optional[str] = None,
    scanner_model: Optional[str] = None,
    scanner_make: Optional[str] = None,
    serial_number: Optional[str] = None,
    creator_tool: str = "JP2Forge",
    operator: Optional[str] = None
) -> Dict[str, Any]:
```

Create BnF-compliant metadata dictionary.

**Parameters:**
- `identifiant`: Document identifier (NUM_XXXXX or IFN_XXXXX format)
- `provenance`: Document owner (default: BnF)
- `ark_identifiant`: ARK identifier
- `cote`: Original document call number
- `scanner_model`: Scanning equipment model
- `scanner_make`: Scanning equipment manufacturer
- `serial_number`: Equipment serial number
- `creator_tool`: Software used for digitization
- `operator`: Digitization operator name

**Returns:**
- `dict`: BnF-compliant metadata dictionary

#### write_bnf_metadata()

```python
def write_bnf_metadata(
    self,
    jp2_file: str,
    metadata: Dict[str, Any],
    compression_mode: str = "supervised",
    num_resolutions: int = 10,
    progression_order: str = "RPCL",
    dcterms_isPartOf: Optional[str] = None,
    dcterms_provenance: str = "Bibliothèque nationale de France",
    dc_relation: Optional[str] = None,
    dc_source: Optional[str] = None
) -> bool:
```

Write BnF-compliant XMP metadata to JP2 file.

**Parameters:**
- `jp2_file`: Path to JPEG2000 file
- `metadata`: Base metadata dictionary
- Additional BnF-specific parameters

**Returns:**
- `bool`: True if successful

**Raises:**
- `FileNotFoundError`: If JP2 file doesn't exist
- `ValueError`: If essential metadata is missing
- `RuntimeError`: If ExifTool operation fails

## 5. Workflow Classes

### BaseWorkflow

Abstract base class for all workflows.

#### process_file()

```python
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
```

Process a single file through the workflow.

#### process_directory()

```python
def process_directory(
    self,
    input_dir: str,
    doc_type: Optional[DocumentType] = None,
    metadata: Optional[Dict[str, Any]] = None,
    recursive: Optional[bool] = None,
    # ... additional parameters
) -> Dict[str, Any]:
```

Process all files in a directory.

### StandardWorkflow

Sequential processing workflow.

```python
class StandardWorkflow(BaseWorkflow):
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
```

### ParallelWorkflow

Parallel processing workflow with worker pools.

```python
class ParallelWorkflow(BaseWorkflow):
    def __init__(self, config: WorkflowConfig):
        super().__init__(config)
        # Initialize worker pool based on configuration
```

## 6. Utility Functions

### Image Utilities

#### validate_image()

```python
@lru_cache(maxsize=100)
def validate_image(input_file: str) -> Tuple[bool, str]:
    """Validate image file integrity with caching."""
```

#### should_process_in_chunks()

```python
def should_process_in_chunks(
    input_file: str, 
    memory_limit_mb: int
) -> Tuple[bool, Optional[int]]:
    """Determine if image should be processed in chunks."""
```

#### is_multipage_tiff()

```python
def is_multipage_tiff(input_file: str) -> Tuple[bool, int]:
    """Check if TIFF file contains multiple pages."""
```

#### extract_tiff_page()

```python
def extract_tiff_page(
    input_file: str, 
    page_num: int, 
    output_dir: str
) -> str:
    """Extract specific page from multi-page TIFF."""
```

### Quality Metrics

#### calculate_psnr()

```python
def calculate_psnr(mse: float) -> float:
    """Calculate Peak Signal-to-Noise Ratio."""
```

#### calculate_ssim()

```python
def calculate_ssim(
    orig_array: np.ndarray, 
    conv_array: np.ndarray
) -> float:
    """Calculate Structural Similarity Index."""
```

#### calculate_mse()

```python
def calculate_mse(
    orig_array: np.ndarray, 
    conv_array: np.ndarray
) -> float:
    """Calculate Mean Square Error."""
```

### File Operations

#### get_output_path()

```python
def get_output_path(
    input_file: str, 
    output_dir: str, 
    extension: str
) -> str:
    """Generate output path with collision handling."""
```

#### find_image_files()

```python
def find_image_files(
    directory: str, 
    recursive: bool = False
) -> List[str]:
    """Find image files in directory."""
```

### BnF Utilities

#### BnFCompressionRatio

```python
class BnFCompressionRatio:
    SPECIALIZED = 4.0
    EXCEPTIONAL = 4.0
    PRINTED = 6.0
    TRANSPARENT = 16.0
    
    @staticmethod
    def get_ratio_for_type(doc_type: DocumentType) -> float:
        """Get BnF compression ratio for document type."""
```

## Usage Examples

### Basic Image Conversion

```python
from core.compressor import JPEG2000Compressor
from core.types import DocumentType, CompressionMode

compressor = JPEG2000Compressor()
success = compressor.convert_to_jp2(
    input_file="image.tif",
    output_file="image.jp2",
    doc_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)
```

### Quality Analysis

```python
from core.analyzer import ImageAnalyzer

analyzer = ImageAnalyzer(psnr_threshold=45.0)
result = analyzer.analyze_pixel_loss(
    original_path="original.tif",
    converted_path="converted.jp2",
    save_report=True
)

print(f"Quality passed: {result.quality_passed}")
print(f"PSNR: {result.psnr:.2f} dB")
```

### BnF-Compliant Processing

```python
from core.metadata import get_metadata_handler
from workflow.standard import StandardWorkflow

# Create BnF metadata
bnf_handler = get_metadata_handler(bnf_compliant=True)
metadata = bnf_handler.create_bnf_compliant_metadata(
    identifiant="NUM_123456",
    provenance="Bibliothèque nationale de France",
    ark_identifiant="ark:/12148/cb123456789",
    cote="FOL-Z-123"
)

# Configure workflow for BnF compliance
config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    bnf_compliant=True,
    compression_mode=CompressionMode.BNF_COMPLIANT
)

workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif", metadata=metadata)
```
