# JP2Forge Examples

This directory contains example scripts demonstrating key JP2Forge features and use cases.

## Quick Reference

| Example Script | Purpose | Key Feature |
|----------------|---------|-------------|
| [`multipage_tiff_conversion.py`](#multipage_tiff_conversionpy) | Convert multi-page TIFFs | Page-by-page processing |
| [`test_all_parameters.py`](#test_all_parameterspy) | Demonstrate all options | Comprehensive configuration |
| [`test_multipage.py`](#test_multipagepy) | Multi-page options | Memory-efficient handling |
| [`test_parameter_fixes.py`](#test_parameter_fixespy) | Fix common issues | Problem remediation |
| [`validate_jp2.py`](#validate_jp2py) | Validate JP2 files | Standards compliance |

## Example Details

### `multipage_tiff_conversion.py`

**Purpose:** Convert multi-page TIFF files to JPEG2000 with efficient page handling.

```bash
python multipage_tiff_conversion.py path/to/multipage.tif output_directory/
```

Key features:
- ✓ Multi-page TIFF detection
- ✓ Page extraction and processing
- ✓ Memory-efficient handling
- ✓ Page-specific metadata

### `test_all_parameters.py`

**Purpose:** Demonstrate all available JP2Forge configuration options.

```bash
python test_all_parameters.py path/to/input.tif output_directory/
```

Key features:
- ✓ Compression options
- ✓ Document type selection
- ✓ Metadata configuration
- ✓ Advanced JP2 parameters

### `test_multipage.py`

**Purpose:** Test multi-page TIFF processing with various options.

```bash
python test_multipage.py path/to/multipage.tif output_directory/ --memory-limit-mb 2048
```

Key features:
- ✓ Chunk size configuration
- ✓ Memory limit settings
- ✓ Page naming options
- ✓ Multi-page metadata handling

### `test_parameter_fixes.py`

**Purpose:** Demonstrate fixes for common conversion issues.

```bash
python test_parameter_fixes.py path/to/problematic_image.tif output_directory/
```

Key features:
- ✓ Color profile handling
- ✓ Problematic image correction
- ✓ Error recovery options
- ✓ Special case handling

### `validate_jp2.py`

**Purpose:** Validate JPEG2000 files against standards.

```bash
python validate_jp2.py path/to/image.jp2
```

Key features:
- ✓ JP2 validation with jpylyzer
- ✓ BnF compliance checking
- ✓ Metadata validation
- ✓ Structural verification

## Usage Tips

- Run `python example_name.py --help` for detailed options
- Examples can be modified and integrated into your own workflows
- All examples follow JP2Forge best practices

## Integration Example

```python
from core.types import WorkflowConfig, DocumentType
from workflow.standard import StandardWorkflow

# Create configuration
config = WorkflowConfig(
    output_dir="output_dir/",
    document_type=DocumentType.PHOTOGRAPH
)

# Create workflow and process
workflow = StandardWorkflow(config)
result = workflow.process_file("input.tif")
print(f"Conversion completed with status: {result.status}")
```