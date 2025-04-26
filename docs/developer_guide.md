# JP2Forge Developer Guide

This guide provides detailed information for developers who want to maintain, extend, or contribute to the JP2Forge project.

## Table of Contents

1. [Development Environment Setup](#1-development-environment-setup)
2. [Project Structure](#2-project-structure)
3. [Core Components](#3-core-components)
4. [Workflow System](#4-workflow-system)
5. [Utility Components](#5-utility-components)
6. [BnF Compliance](#6-bnf-compliance)
7. [Testing Strategy](#7-testing-strategy)
8. [Code Style Guidelines](#8-code-style-guidelines)
9. [Contributing Guidelines](#9-contributing-guidelines)
10. [Documentation Guidelines](#10-documentation-guidelines)

## 1. Development Environment Setup

### 1.1 Prerequisites

* Python 3.9 or newer
* Git
* ExifTool (for metadata handling)
* Kakadu (optional, for BnF-compliant compression)

### 1.2 Setting Up Development Environment

1. **Clone the repository**:

   ```bash
   git clone https://github.com/xy-liao/jp2forge.git
   cd jp2forge
   ```

2. **Create a virtual environment** (recommended):

   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Or using conda
   conda create -n jp2forge python=3.9
   conda activate jp2forge
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Install external tools**:

   ```bash
   # On macOS
   brew install exiftool

   # On Ubuntu/Debian
   sudo apt install libimage-exiftool-perl

   # On Windows
   # Download and install from https://exiftool.org
   ```

5. **Set up pre-commit hooks** (optional but recommended):

   ```bash
   pre-commit install
   ```

### 1.3 Development Tools

- **IDE**: VS Code with Python extension is recommended
- **Debugging**: Use the Python debugger (`pdb`) or an IDE debugger
- **Code Quality**: Use flake8, black, and isort for code formatting and linting
- **Testing**: pytest for unit and integration testing

## 2. Project Structure

JP2Forge follows a modular structure organized by functionality:

```
jp2forge/
├── cli/                  # Command-line interface
│   ├── __init__.py
│   └── workflow.py       # CLI entry point
├── core/                 # Core functionality
│   ├── __init__.py
│   ├── analyzer.py       # Image quality analysis
│   ├── compressor.py     # JPEG2000 compression
│   ├── metadata/         # Metadata handling
│   │   ├── __init__.py
│   │   ├── base_handler.py
│   │   ├── bnf_handler.py
│   │   └── xmp_utils.py
│   ├── metadata.py       # Legacy metadata module
│   └── types.py          # Core type definitions
├── docs/                 # Documentation
│   ├── architecture.md   # System architecture
│   ├── developer_guide.md # This guide
│   └── user_guide.md     # End-user documentation
├── tests/                # Test suite
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_compressor.py
│   └── ...
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── config/           # Configuration management
│   ├── imaging/          # Image processing utilities
│   ├── parallel/         # Parallel processing
│   ├── tools/            # External tool management
│   └── xml/              # XML processing utilities
├── workflow/             # Workflow orchestration
│   ├── __init__.py
│   ├── base.py           # Base workflow
│   ├── parallel.py       # Parallel workflow
│   └── standard.py       # Standard workflow
├── .gitignore            # Git ignore file
├── AUTHORS               # Contributors list
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # Contribution guidelines
├── IMPROVEMENTS.md       # Improvement documentation
├── LICENSE               # License file
├── README.md             # Project overview
├── requirements.txt      # Dependencies
└── requirements-dev.txt  # Development dependencies
```

## 3. Core Components

### 3.1 Compressor (`core.compressor`)

The compressor module handles the conversion of images to JPEG2000 format:

```python
from core.compressor import JP2Compressor

# Create a compressor instance
compressor = JP2Compressor()

# Compress an image
compressor.compress(
    input_path='input.tif',
    output_path='output.jp2',
    parameters={
        'compression_mode': 'lossy',
        'quality': 40.0
    }
)
```

#### Key Classes

- `JP2Compressor`: Base compressor implementation using Pillow
- `BnFCompressor`: BnF-compliant compressor using Kakadu (when available)

#### Extension Points

To implement a custom compression strategy:

```python
from core.compressor import JP2Compressor

class CustomCompressor(JP2Compressor):
    def compress(self, input_path, output_path, parameters=None):
        # Custom compression implementation
        pass
```

### 3.2 Analyzer (`core.analyzer`)

The analyzer module evaluates the quality of compressed images:

```python
from core.analyzer import QualityAnalyzer

# Create an analyzer instance
analyzer = QualityAnalyzer()

# Analyze compression quality
results = analyzer.analyze(
    original_path='input.tif',
    compressed_path='output.jp2'
)

print(f"PSNR: {results.psnr:.2f} dB")
print(f"SSIM: {results.ssim:.4f}")
```

#### Key Classes

- `QualityAnalyzer`: Calculates quality metrics for compressed images
- `CompressionRatioValidator`: Validates BnF compression ratio requirements

#### Adding New Metrics

To add a new quality metric:

```python
from core.analyzer import QualityAnalyzer

class EnhancedAnalyzer(QualityAnalyzer):
    def analyze(self, original_path, compressed_path):
        # Get base metrics
        results = super().analyze(original_path, compressed_path)
        
        # Add custom metric
        results.custom_metric = self._calculate_custom_metric(
            original_path, compressed_path
        )
        
        return results
    
    def _calculate_custom_metric(self, original_path, compressed_path):
        # Implementation of custom metric calculation
        pass
```

### 3.3 Metadata (`core.metadata`)

The metadata module handles embedding metadata in JPEG2000 files:

```python
from core.metadata.base_handler import MetadataHandler

# Create a metadata handler
handler = MetadataHandler()

# Inject metadata
handler.inject_metadata(
    jp2_path='output.jp2',
    metadata={
        'xmp:CreatorTool': 'JP2Forge',
        'xmp:CreateDate': '2023-05-25T12:00:00Z'
    }
)
```

#### Key Classes

- `MetadataHandler`: Base metadata handling
- `BnFMetadataHandler`: BnF-compliant metadata handling
- `XMPUtils`: Utilities for XMP metadata generation

#### Implementing Custom Metadata Handler

```python
from core.metadata.base_handler import MetadataHandler

class CustomMetadataHandler(MetadataHandler):
    def inject_metadata(self, jp2_path, metadata):
        # Custom metadata injection logic
        pass
    
    def extract_metadata(self, jp2_path):
        # Custom metadata extraction logic
        pass
```

## 4. Workflow System

### 4.1 BaseWorkflow (`workflow.base`)

The BaseWorkflow provides the foundation for all workflows:

```python
from workflow.base import BaseWorkflow
from core.types import WorkflowConfig

# Create a workflow configuration
config = WorkflowConfig(
    output_dir='output_dir/',
    report_dir='reports/'
)

# BaseWorkflow is abstract and must be subclassed
class MyWorkflow(BaseWorkflow):
    def process_file(self, input_path):
        # Implementation of file processing
        pass
```

#### Key Methods

- `process_file(input_path)`: Process a single file
- `process_directory(directory_path, recursive=False)`: Process all files in a directory
- `_validate_input_path(path)`: Validate an input path
- `_validate_output_path(path)`: Validate and create an output path

### 4.2 StandardWorkflow (`workflow.standard`)

The StandardWorkflow implements the standard processing pipeline:

```python
from workflow.standard import StandardWorkflow
from core.types import WorkflowConfig, DocumentType, CompressionMode

# Create configuration
config = WorkflowConfig(
    output_dir='output_dir/',
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)

# Create workflow
workflow = StandardWorkflow(config)

# Process a file
result = workflow.process_file('input.tif')

print(f"Status: {result.status}")
print(f"PSNR: {result.psnr:.2f} dB")
```

### 4.3 ParallelWorkflow (`workflow.parallel`)

The ParallelWorkflow handles batch processing with resource-aware parallelism:

```python
from workflow.parallel import ParallelWorkflow
from core.types import WorkflowConfig, ProcessingMode

# Create configuration
config = WorkflowConfig(
    output_dir='output_dir/',
    processing_mode=ProcessingMode.PARALLEL,
    max_workers=4,
    adaptive_workers=True
)

# Create workflow
workflow = ParallelWorkflow(config)

# Set up progress callback
def progress_callback(progress_data):
    print(f"Progress: {progress_data['percent_complete']:.1f}%")
    print(f"ETA: {progress_data['eta_time']}")

# Process directory
results = workflow.process_directory(
    'input_dir/',
    recursive=True,
    progress_callback=progress_callback
)
```

#### Customizing Parallel Processing

```python
from workflow.parallel import ParallelWorkflow
from utils.parallel.resource_monitor import ResourceMonitor

class CustomParallelWorkflow(ParallelWorkflow):
    def _initialize_worker_pool(self):
        # Custom worker pool initialization
        pool = super()._initialize_worker_pool()
        
        # Custom resource monitor settings
        monitor = ResourceMonitor(
            cpu_threshold=0.85,
            memory_threshold=0.90,
            update_interval=2.0
        )
        pool.set_resource_monitor(monitor)
        
        return pool
```

## 5. Utility Components

### 5.1 Configuration (`utils.config`)

The configuration system manages application settings:

```python
from utils.config.config_manager import ConfigManager

# Create config manager
config_manager = ConfigManager()

# Load from different sources
config_manager.load_from_file('config.yaml')
config_manager.load_from_env(prefix='JP2FORGE_')

# Get configuration values
output_dir = config_manager.get('output.directory', 'default/')
compression_mode = config_manager.get('compression.mode', 'supervised')

# Get full configuration
config_dict = config_manager.get_config()
```

### 5.2 Parallel Processing (`utils.parallel`)

The parallel processing utilities implement resource-aware concurrency:

```python
from utils.parallel.adaptive_pool import AdaptiveWorkerPool
from utils.parallel.resource_monitor import ResourceMonitor

# Create resource monitor
monitor = ResourceMonitor(
    cpu_threshold=0.80,
    memory_threshold=0.85
)

# Create worker pool
pool = AdaptiveWorkerPool(
    min_workers=2,
    max_workers=8,
    resource_monitor=monitor
)

# Submit tasks
for task in tasks:
    pool.submit(task)

# Get results
results = pool.get_all_results()
```

### 5.3 Streaming Image Processing (`utils.imaging`)

The streaming processor handles large images in memory-efficient chunks:

```python
from utils.imaging.streaming_processor import StreamingImageProcessor
from PIL import ImageFilter

# Create processor
processor = StreamingImageProcessor(
    memory_limit_mb=2048,
    min_chunk_height=32
)

# Define processing function
def enhance_image(chunk):
    return chunk.filter(ImageFilter.SHARPEN)

# Process large image
processor.process_in_chunks(
    'large_image.tif',
    'output.jp2',
    enhance_image,
    save_kwargs={'quality': 90}
)
```

### 5.4 Tool Management (`utils.tools`)

The tool management system handles external tool integration:

```python
from utils.tools.tool_manager import ToolManager
from utils.tools.kakadu_tool import KakaduTool

# Get tool manager
manager = ToolManager()

# Check for tool availability
has_exiftool = manager.has_tool('exiftool')
has_kakadu = manager.has_tool('kakadu')

# Get tool instances
exiftool = manager.get_tool('exiftool')
kakadu = manager.get_tool('kakadu')

# Or create custom tool
custom_kakadu = KakaduTool(
    executable_path='/opt/kakadu/kdu_compress',
    working_dir='/tmp'
)
```

## 6. BnF Compliance

JP2Forge provides specialized support for BnF compliance requirements:

### 6.1 BnF Compression Parameters

```python
from core.types import DocumentType
from workflow.standard import StandardWorkflow
from core.types import WorkflowConfig

# Create BnF-compliant configuration
config = WorkflowConfig(
    output_dir='output_dir/',
    document_type=DocumentType.PHOTOGRAPH,  # Sets 1:4 ratio
    bnf_compliant=True,
    compression_ratio_tolerance=0.05  # 5% tolerance
)

# Create workflow
workflow = StandardWorkflow(config)

# Process files
result = workflow.process_file('input.tif')
```

### 6.2 BnF Metadata Requirements

```python
from core.metadata.bnf_handler import BnFMetadataHandler

# Create BnF metadata handler
handler = BnFMetadataHandler()

# Prepare BnF-compliant metadata
metadata = {
    'dcterms:isPartOf': 'NUM_123456',
    'dcterms:provenance': 'Bibliothèque nationale de France',
    'dc:relation': 'ark:/12148/cb123456789',
    'dc:source': 'FOL-Z-123',
    'tiff:Model': 'PhaseOne P45+',
    'tiff:Make': 'Phase One',
    'aux:SerialNumber': '1234567890',
    'xmp:CreatorTool': 'JP2Forge 2.0',
    'xmp:CreateDate': '2023-05-25T12:00:00Z',
    'xmp:ModifyDate': '2023-05-25T14:30:00Z',
    'tiff:Artist': 'Image Digitization Operator'
}

# Inject metadata
handler.inject_metadata('output.jp2', metadata)

# Validate BnF compliance
is_compliant = handler.validate_bnf_compliance('output.jp2')
```

### 6.3 Using Kakadu for BnF Compliance

```python
from workflow.standard import StandardWorkflow
from core.types import WorkflowConfig
from utils.tools.kakadu_tool import KakaduTool

# Create Kakadu tool
kakadu = KakaduTool(executable_path='/path/to/kdu_compress')

# Configure workflow
config = WorkflowConfig(
    output_dir='output_dir/',
    bnf_compliant=True,
    use_kakadu=True,
    kakadu_tool=kakadu
)

# Create and run workflow
workflow = StandardWorkflow(config)
result = workflow.process_file('input.tif')
```

## 7. Testing Strategy

JP2Forge uses pytest for unit and integration testing:

### 7.1 Unit Tests

Unit tests focus on isolated component testing:

```python
# tests/test_analyzer.py
import pytest
from core.analyzer import QualityAnalyzer

def test_psnr_calculation():
    analyzer = QualityAnalyzer()
    # Use test images
    psnr = analyzer.calculate_psnr('tests/data/original.tif', 
                                 'tests/data/compressed.jp2')
    assert psnr > 0
    
def test_ssim_calculation():
    analyzer = QualityAnalyzer()
    ssim = analyzer.calculate_ssim('tests/data/original.tif', 
                                 'tests/data/compressed.jp2')
    assert 0 <= ssim <= 1
```

### 7.2 Integration Tests

Integration tests verify component interactions:

```python
# tests/test_workflow.py
import pytest
import os
from workflow.standard import StandardWorkflow
from core.types import WorkflowConfig

@pytest.fixture
def test_workflow():
    config = WorkflowConfig(
        output_dir='tests/output',
        report_dir='tests/reports'
    )
    return StandardWorkflow(config)

def test_end_to_end_processing(test_workflow):
    # Clean output directory
    os.makedirs('tests/output', exist_ok=True)
    
    # Process test file
    result = test_workflow.process_file('tests/data/test_image.tif')
    
    # Verify output exists
    output_path = os.path.join('tests/output', 'test_image.jp2')
    assert os.path.exists(output_path)
    
    # Verify quality metrics
    assert result.status == 'SUCCESS'
    assert result.psnr > 30.0  # Good quality threshold
```

### 7.3 Running Tests

To run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_analyzer.py

# Run with coverage report
pytest --cov=.

# Run tests matching specific pattern
pytest -k "analyzer or metadata"
```

## 8. Code Style Guidelines

JP2Forge follows these code style guidelines:

### 8.1 PEP 8 Compliance

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style
- 4 spaces for indentation (no tabs)
- 79 character line limit for code
- 72 character line limit for docstrings/comments
- Use appropriate naming conventions:
  - `snake_case` for variables, functions, and methods
  - `PascalCase` for classes
  - `UPPER_CASE` for constants

### 8.2 Docstrings

Use Google-style docstrings:

```python
def process_image(input_path, output_path, quality=90):
    """Process an image with the specified quality.
    
    Args:
        input_path (str): Path to the input image file.
        output_path (str): Path where the processed image will be saved.
        quality (int, optional): Quality level (0-100). Defaults to 90.
        
    Returns:
        bool: True if processing was successful, False otherwise.
        
    Raises:
        ValueError: If quality is outside the range 0-100.
        FileNotFoundError: If input_path doesn't exist.
    """
```

### 8.3 Type Hints

Use type hints for function signatures:

```python
from typing import Dict, List, Optional, Union

def analyze_image(
    image_path: str,
    metrics: List[str] = ['psnr', 'ssim'],
    parameters: Optional[Dict[str, Union[int, float, str]]] = None
) -> Dict[str, float]:
    """Analyze an image using specified metrics."""
```

### 8.4 Code Organization

- Organize imports in groups: standard library, third-party, local
- Group related functionality in classes and modules
- Keep functions focused on a single responsibility
- Use meaningful variable names that describe purpose, not type

## 9. Contributing Guidelines

To contribute to JP2Forge:

### 9.1 Getting Started

1. Fork the repository on GitHub
2. Clone your fork: `git clone https://github.com/your-username/jp2forge.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `pip install -r requirements-dev.txt`

### 9.2 Development Workflow

1. Make your changes, following the code style guidelines
2. Add tests for new functionality
3. Ensure all tests pass: `pytest`
4. Update documentation as needed
5. Run code quality checks: `flake8` and `black .`

### 9.3 Pull Request Process

1. Push your changes to your fork
2. Submit a pull request to the main repository
3. Reference any related issues
4. Ensure the CI pipeline passes
5. Wait for code review and address feedback
6. Once approved, your changes will be merged

### 9.4 Commit Message Guidelines

Follow conventional commits pattern:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or modifying tests
- `chore:` for build process or tool changes

Example: `feat: Add support for CMYK color space in compression`

## 10. Documentation Guidelines

JP2Forge documentation follows these guidelines:

### 10.1 Code Documentation

- All public classes, methods, and functions must have docstrings
- Use type hints for function parameters and return values
- Document parameters, return values, and exceptions
- Include examples in docstrings for complex functionality

### 10.2 External Documentation

- `README.md`: Project overview, quick start, basic usage
- `docs/architecture.md`: System architecture and design
- `docs/developer_guide.md`: This guide for developers
- `docs/user_guide.md`: Detailed instructions for end users
- `CHANGELOG.md`: Version history and release notes
- `CONTRIBUTING.md`: Contribution guidelines

### 10.3 Documentation Format

- Use Markdown for all documentation files
- Follow a consistent structure with clear headings
- Include examples for common use cases
- Keep documentation up-to-date with code changes

### 10.4 Documentation Checklist

Before submitting changes, ensure:

- All new functionality is documented
- Examples are provided for complex features
- Documentation reflects the actual implementation
- Code samples in documentation work as expected
- Docstrings follow the established format
