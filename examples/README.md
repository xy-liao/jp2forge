# JP2Forge Examples

This directory contains practical examples demonstrating various JP2Forge features and use cases.

## Available Examples

### 1. `validate_jp2.py`
**Purpose**: Validate JPEG2000 files using JPylyzer integration

**Usage**:
```bash
python examples/validate_jp2.py output_dir/
```

**Features**:
- Validates all JP2 files in a directory
- Generates validation reports
- Demonstrates JPylyzer integration

### 2. `multipage_tiff_conversion.py`
**Purpose**: Convert multi-page TIFF files to individual JP2 files

**Usage**:
```bash
python examples/multipage_tiff_conversion.py multipage.tif output_dir/
```

**Features**:
- Handles multi-page TIFF extraction
- Individual JP2 conversion for each page
- Memory-efficient processing

### 3. `test_multipage.py`
**Purpose**: Test multi-page TIFF processing with different configurations

**Usage**:
```bash
python examples/test_multipage.py
```

**Features**:
- Tests various multi-page scenarios
- Performance benchmarking
- Error handling validation

### 4. `test_all_parameters.py`
**Purpose**: Comprehensive testing of all JP2Forge parameters

**Usage**:
```bash
python examples/test_all_parameters.py
```

**Features**:
- Tests all compression modes
- Document type variations
- BnF compliance verification
- Parallel processing tests

### 5. `test_parameter_fixes.py`
**Purpose**: Validate parameter handling and fixes

**Usage**:
```bash
python examples/test_parameter_fixes.py
```

**Features**:
- Parameter validation tests
- Edge case handling
- Configuration validation

## Running Examples

### Prerequisites

Ensure JP2Forge is properly installed and configured:

```bash
# Install JP2Forge dependencies
pip install -r requirements.txt

# Ensure ExifTool is available
# macOS: brew install exiftool
# Linux: sudo apt install libimage-exiftool-perl
```

### Basic Example Usage

```bash
# Navigate to JP2Forge directory
cd jp2forge

# Run validation example
python examples/validate_jp2.py output_dir/

# Convert multi-page TIFF
python examples/multipage_tiff_conversion.py input.tif output_dir/

# Test all parameters
python examples/test_all_parameters.py
```

### API Examples

Each example also demonstrates programmatic usage of JP2Forge components:

```python
# Example: Basic conversion
from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

config = WorkflowConfig(
    output_dir="output/",
    report_dir="reports/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)

workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif")
```

### Custom Examples

You can create custom examples by following these patterns:

```python
#!/usr/bin/env python3
"""
Custom JP2Forge Example
"""

import sys
import os

# Add JP2Forge to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

def main():
    # Your custom processing logic here
    config = WorkflowConfig(
        output_dir="custom_output/",
        report_dir="custom_reports/",
        document_type=DocumentType.HERITAGE_DOCUMENT,
        compression_mode=CompressionMode.LOSSLESS
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file("your_input.tif")
    
    if result.status.name == "SUCCESS":
        print(f"Successfully converted: {result.output_file}")
    else:
        print(f"Conversion failed: {result.error}")

if __name__ == "__main__":
    main()
```

## Example Output

Each example produces output in standard JP2Forge format:

```
output_dir/          # Converted JP2 files
reports/             # Processing reports
├── info_jpylyzer.json    # JPylyzer validation results
├── summary_report.md     # Human-readable summary
└── analysis_*.json       # Individual file analysis
```

## Troubleshooting

If examples fail to run:

1. **Check dependencies**: Ensure all required packages are installed
2. **Verify paths**: Make sure input files exist and output directories are writable
3. **ExifTool availability**: Verify ExifTool is installed and accessible
4. **Python path**: Run examples from the JP2Forge root directory

## Contributing Examples

To contribute new examples:

1. Create a new Python file in the `examples/` directory
2. Include clear docstrings and comments
3. Add usage instructions to this README
4. Test with various input types and edge cases
5. Submit a pull request

Example template:

```python
#!/usr/bin/env python3
"""
Example Name: Brief description

Purpose:
    Detailed explanation of what this example demonstrates

Usage:
    python examples/your_example.py [arguments]

Requirements:
    - List any special requirements
    - Additional dependencies
    - System requirements
"""

# Your example code here
```
