# JP2Forge Developer Guide

This guide provides technical information for developers working with JP2Forge.

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Components](#2-core-components)
3. [Development Setup](#3-development-setup)
4. [API Usage](#4-api-usage)
5. [Extension Points](#5-extension-points)
6. [Testing Strategy](#6-testing-strategy)
7. [Code Quality](#7-code-quality)

## 1. Architecture Overview

JP2Forge follows a modular architecture with clear separation of concerns:

```
jp2forge/
├── cli/                    # Command-line interface
├── core/                   # Core functionality
│   ├── compressor.py      # JPEG2000 compression
│   ├── analyzer.py        # Quality analysis
│   ├── metadata/          # Metadata handling
│   └── types.py           # Type definitions
├── workflow/              # Processing workflows
│   ├── base.py           # Base workflow class
│   ├── standard.py   # Sequential processing
│   ├── parallel.py       # Parallel processing
│   └── utils.py          # Shared workflow utilities
├── utils/                 # Utility functions
└── examples/              # Usage examples
```

### Key Design Principles

- **Modularity**: Each component has a specific responsibility
- **Extensibility**: Easy to add new compression modes or document types
- **Configuration**: Flexible configuration system
- **Error Handling**: Comprehensive error handling and logging
- **Code Reusability**: Shared utilities to eliminate duplication

## 2. Core Components

### 2.1 JPEG2000Compressor

Handles image compression to JPEG2000 format:

```python
from core.compressor import JPEG2000Compressor
from core.types import DocumentType, CompressionMode

compressor = JPEG2000Compressor(
    num_resolutions=10,
    progression_order="RPCL"
)

success = compressor.convert_to_jp2(
    input_file="input.tif",
    output_file="output.jp2",
    doc_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)
```

### 2.2 ImageAnalyzer

Provides quality analysis of compressed images:

```python
from core.analyzer import ImageAnalyzer

analyzer = ImageAnalyzer(
    psnr_threshold=40.0,
    ssim_threshold=0.95
)

result = analyzer.analyze_pixel_loss(
    original_path="original.tif",
    converted_path="converted.jp2"
)

print(f"PSNR: {result.psnr:.2f} dB")
print(f"SSIM: {result.ssim:.4f}")
print(f"Quality passed: {result.quality_passed}")
```

### 2.3 MetadataHandler

Manages metadata operations:

```python
from core.metadata import get_metadata_handler

# Standard metadata handler
handler = get_metadata_handler(bnf_compliant=False)

# BnF-compliant metadata handler
bnf_handler = get_metadata_handler(bnf_compliant=True)

# Create BnF metadata
metadata = bnf_handler.create_bnf_compliant_metadata(
    identifiant="NUM_123456",
    provenance="Bibliothèque nationale de France",
    ark_identifiant="ark:/12148/cb123456789",
    cote="FOL-Z-123"
)
```

### 2.4 Workflow Classes

#### StandardWorkflow

Sequential processing of images:

```python
from workflow.standard import StandardWorkflow
from core.types import WorkflowConfig, DocumentType, CompressionMode

config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)

workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif")
```

#### ParallelWorkflow

Parallel processing with worker pools:

```python
from workflow.parallel import ParallelWorkflow
from core.types import ProcessingMode

config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    processing_mode=ProcessingMode.PARALLEL,
    max_workers=4
)

workflow = ParallelWorkflow(config)
results = workflow.process_directory("input_dir/")
```

## 3. Development Setup

### Environment Setup

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=core --cov=workflow --cov=utils

# Run specific test file
pytest tests/test_compressor.py
```

### Code Quality Checks

```bash
# Run linting
flake8 core/ workflow/ utils/

# Format code
black core/ workflow/ utils/

# Type checking
mypy core/ workflow/ utils/
```

## 4. API Usage

### Basic Conversion

```python
from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

# Create configuration
config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED,
    quality_threshold=40.0
)

# Create workflow
workflow = StandardWorkflow(config)

# Process single file
result = workflow.process_file("input.tif")

if result.status.name == "SUCCESS":
    print(f"Converted: {result.output_file}")
else:
    print(f"Error: {result.error}")
```

### BnF-Compliant Processing

```python
from core.types import CompressionMode
from core.metadata import get_metadata_handler

# Configuration for BnF compliance
config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    compression_mode=CompressionMode.BNF_COMPLIANT,
    bnf_compliant=True,
    include_bnf_markers=True
)

# Create BnF metadata
bnf_handler = get_metadata_handler(bnf_compliant=True)
metadata = bnf_handler.create_bnf_compliant_metadata(
    identifiant="NUM_123456",
    provenance="Bibliothèque nationale de France"
)

# Process with BnF compliance
workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif", metadata=metadata)
```

### Custom Processing Pipeline

```python
from core.compressor import JPEG2000Compressor
from core.analyzer import ImageAnalyzer
from core.types import DocumentType, CompressionMode

# Create components
compressor = JPEG2000Compressor(
    num_resolutions=10,
    progression_order="RPCL"
)

analyzer = ImageAnalyzer(
    psnr_threshold=45.0,
    ssim_threshold=0.98
)

# Custom processing
success = compressor.convert_to_jp2(
    input_file="input.tif",
    output_file="output.jp2",
    doc_type=DocumentType.HERITAGE_DOCUMENT,
    compression_mode=CompressionMode.SUPERVISED
)

if success:
    analysis = analyzer.analyze_pixel_loss(
        original_path="input.tif",
        converted_path="output.jp2"
    )
    
    print(f"Quality metrics: PSNR={analysis.psnr:.2f}, SSIM={analysis.ssim:.4f}")
```

## 5. Extension Points

### Adding New Document Types

1. Add to the `DocumentType` enum in `core/types.py`:

```python
class DocumentType(Enum):
    PHOTOGRAPH = auto()
    HERITAGE_DOCUMENT = auto()
    COLOR = auto()
    GRAYSCALE = auto()
    YOUR_NEW_TYPE = auto()  # Add here
```

2. Update compression parameters in `compressor.py`:

```python
def _get_compression_params(self, doc_type, lossless, bnf_compliant=False):
    # ... existing code ...
    elif doc_type == DocumentType.YOUR_NEW_TYPE:
        params.update({
            "quality_mode": "rates",
            "quality_layers": [45, 35, 25]
        })
```

### Adding New Compression Modes

1. Add to the `CompressionMode` enum:

```python
class CompressionMode(Enum):
    LOSSLESS = "lossless"
    LOSSY = "lossy"
    SUPERVISED = "supervised"
    BNF_COMPLIANT = "bnf_compliant"
    YOUR_NEW_MODE = "your_new_mode"  # Add here
```

2. Implement the logic in the compressor:

```python
def convert_to_jp2(self, ...):
    if compression_mode == CompressionMode.YOUR_NEW_MODE:
        # Implement your compression logic here
        pass
```

### Custom Metadata Handlers

Create a new metadata handler by extending `MetadataHandler`:

```python
from core.metadata.base_handler import MetadataHandler

class CustomMetadataHandler(MetadataHandler):
    def __init__(self):
        super().__init__()
    
    def create_custom_metadata(self, custom_fields):
        # Implement custom metadata creation
        pass
    
    def write_custom_metadata(self, jp2_file, metadata):
        # Implement custom metadata writing
        pass
```

## 6. Testing Strategy

### Unit Tests

Test individual components in isolation:

```python
import pytest
from core.compressor import JPEG2000Compressor
from core.types import DocumentType, CompressionMode

class TestJPEG2000Compressor:
    def test_convert_basic(self):
        compressor = JPEG2000Compressor()
        # Test basic conversion
        
    def test_bnf_compliance(self):
        compressor = JPEG2000Compressor()
        # Test BnF-compliant conversion
        
    def test_error_handling(self):
        compressor = JPEG2000Compressor()
        # Test error conditions
```

### Integration Tests

Test component interactions:

```python
def test_full_workflow():
    config = WorkflowConfig(
        output_dir="test_output/",
        report_dir="test_reports/"
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file("test_input.tif")
    
    assert result.status.name == "SUCCESS"
    assert os.path.exists(result.output_file)
```

### Test Data

Organize test data by category:

```
tests/
├── data/
│   ├── images/
│   │   ├── small_test.tif
│   │   ├── large_test.tif
│   │   └── multipage_test.tif
│   ├── metadata/
│   │   ├── basic_metadata.json
│   │   └── bnf_metadata.json
│   └── expected/
│       ├── small_test.jp2
│       └── quality_report.json
└── test_*.py
```

## 7. Code Quality

### Code Style Guidelines

- Follow PEP 8 for Python code style
- Use Google-style docstrings for all functions and classes
- Include type hints for function parameters and return values
- Keep functions under 50 lines when possible
- Use descriptive variable and function names

### Documentation Standards

```python
def convert_to_jp2(
    self,
    input_file: str,
    output_file: str,
    doc_type: DocumentType,
    compression_mode: CompressionMode = CompressionMode.SUPERVISED
) -> bool:
    """Convert image to JPEG2000 format.
    
    Args:
        input_file: Path to input image
        output_file: Path for output JP2 file
        doc_type: Type of document being processed
        compression_mode: Compression mode to use
        
    Returns:
        bool: True if conversion successful
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If conversion fails critically
    """
```

### Error Handling

Use specific exception types and provide meaningful error messages:

```python
class JP2ForgeError(Exception):
    """Base exception for JP2Forge errors."""
    pass

class CompressionError(JP2ForgeError):
    """Error during image compression."""
    pass

class MetadataError(JP2ForgeError):
    """Error during metadata operations."""
    pass

# Usage
try:
    result = compressor.convert_to_jp2(...)
except FileNotFoundError as e:
    logger.error(f"Input file not found: {e}")
    raise CompressionError(f"Cannot process missing file: {input_file}") from e
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise CompressionError(f"Compression failed: {e}") from e
```

### Logging

Use structured logging throughout the codebase:

```python
import logging
logger = logging.getLogger(__name__)

# Good logging practices
logger.info(f"Processing file: {input_file}")
logger.debug(f"Using compression parameters: {params}")
logger.warning(f"Quality below threshold: PSNR={psnr:.2f}")
logger.error(f"Failed to process {input_file}: {error}")
```

### Performance Considerations

- Use generators for large datasets
- Implement proper memory management with context managers
- Profile critical code paths
- Use appropriate data structures for the task

```python
# Memory-efficient file processing
def process_large_files(file_list):
    """Process files one at a time to manage memory."""
    for file_path in file_list:
        with MemoryManager() as mem:
            yield process_single_file(file_path)
            mem.cleanup()
```
