# JPylyzer Integration in JP2Forge

This document describes how to use the JPylyzer integration in JP2Forge for JPEG2000 validation and property extraction.

## Overview

[JPylyzer](https://jpylyzer.openpreservation.org/) is a powerful JP2 (JPEG 2000 Part 1) image validator and properties extractor. JP2Forge integrates JPylyzer as an external tool to provide comprehensive validation capabilities for JPEG2000 files.

## Requirements

To use JPylyzer with JP2Forge, you need one of the following:

1. **JPylyzer as a command-line tool** - The system will try to locate it automatically in your PATH.
2. **JPylyzer as a Python module** - If the executable is not found, JP2Forge will attempt to use the Python module if installed (`pip install jpylyzer`).

## Features

The JP2Forge JPylyzer integration provides the following features:

- **Validation** of JP2 files against the JPEG2000 standard
- **Property extraction** from JP2 files
- Support for various JPEG2000 formats (`jp2`, `j2c`, `jph`, `jhc`)
- Graceful fallback to basic validation when JPylyzer is not available

## Usage Examples

### Using the JP2Validator class

The `JP2Validator` class is the main interface for JPylyzer integration:

```python
from utils.tools.tool_manager import ToolManager
from utils.validation import JP2Validator

# Initialize ToolManager to detect JPylyzer automatically
tool_manager = ToolManager(prefer_system_tools=True)

# Initialize the validator
validator = JP2Validator(tool_manager=tool_manager)

# Validate a JP2 file
result = validator.validate_jp2('path/to/image.jp2')

# Check if the file is valid
is_valid = result.get('isValid', False)

# Extract properties (same as validate_jp2)
properties = validator.extract_properties('path/to/image.jp2')

# Get image dimensions from properties
width, height = validator.get_image_dimensions(properties)

# Quick validity check
if validator.is_valid_jp2('path/to/image.jp2'):
    print("The file is a valid JP2")
```

### Manual JPylyzer tool initialization

If you need more control over the JPylyzer integration:

```python
from utils.tools.jpylyzer_tool import JPylyzerTool

# Initialize with custom path
jpylyzer = JPylyzerTool(
    jpylyzer_path='/path/to/jpylyzer',
    timeout=120,
    format_type='jp2'  # Supports: 'jp2', 'j2c', 'jph', 'jhc'
)

# Validate a file
result = jpylyzer.validate('path/to/image.jp2')

# Extract properties (same as validate)
properties = jpylyzer.extract_properties('path/to/image.jp2')
```

## Command-line Example

JP2Forge includes a simple command-line tool for validating JP2 files:

```bash
python examples/validate_jp2.py path/to/image.jp2 --format jp2 --verbose
```

Options:
- `--format`: JPEG2000 format type (`jp2`, `j2c`, `jph`, `jhc`)
- `--verbose`: Print detailed validation information
- `--output`: Save full results to a JSON file

## Integration with Workflows

You can integrate JPylyzer validation into your JP2Forge workflows:

```python
from workflow.standard import StandardWorkflow
from utils.validation import JP2Validator

# Create workflow
workflow = StandardWorkflow()

# Add validation step
validator = JP2Validator()

def validate_step(context):
    for file_path in context.get('input_files', []):
        if file_path.endswith('.jp2'):
            result = validator.validate_jp2(file_path)
            if not result.get('isValid', False):
                context['errors'].append(f"Invalid JP2 file: {file_path}")
    return context

# Register validation step
workflow.register_step('validate_jp2', validate_step)
```

## Output Format

The validation output follows the JPylyzer XML structure, converted to a Python dictionary:

```python
{
    "toolInfo": {
        "toolName": "jpylyzer",
        "toolVersion": "2.0.0"
    },
    "fileInfo": {
        "fileName": "example.jp2",
        "filePath": "/path/to/example.jp2",
        "fileSize": 1048576
    },
    "isValid": True,
    "tests": {
        # Test results organized by box
    },
    "properties": {
        # File properties organized by box
    },
    "warnings": [
        # Any warnings
    ]
}
```

## Fallback Behavior

When JPylyzer is not available, the system falls back to basic validation, which:
- Checks file existence and size
- Verifies the JPEG2000 signature in the file header
- Returns limited properties

## Further Resources

- [JPylyzer Official Documentation](https://jpylyzer.openpreservation.org/)
- [JPEG2000 Part 1 Standard](https://www.itu.int/rec/T-REC-T.800)