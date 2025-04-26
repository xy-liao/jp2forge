# JP2Forge Examples

This directory contains example scripts that demonstrate various features and use cases of JP2Forge. These examples are designed to help users understand how to effectively use JP2Forge for different scenarios.

## Example Files Overview

### `multipage_tiff_conversion.py`

Demonstrates how to convert multi-page TIFF files to JPEG2000 format with page-by-page processing.

**Key features demonstrated:**
- Multi-page TIFF detection and handling
- Page extraction and individual processing
- Memory-efficient processing for large TIFF files
- Metadata handling for multi-page documents

**Usage:**
```bash
python multipage_tiff_conversion.py path/to/multipage.tif output_directory/
```

### `test_all_parameters.py`

A comprehensive example that demonstrates all available configuration parameters for JP2Forge.

**Key features demonstrated:**
- Full range of compression options
- Document type selection
- Metadata configuration
- Advanced JPEG2000 parameters

**Usage:**
```bash
python test_all_parameters.py path/to/input.tif output_directory/
```

### `test_multipage.py`

Tests and demonstrates various options specifically for multi-page TIFF processing.

**Key features demonstrated:**
- Chunk size configuration
- Memory limit settings
- Page naming options
- Multi-page specific metadata handling

**Usage:**
```bash
python test_multipage.py path/to/multipage.tif output_directory/ --memory-limit-mb 2048
```

### `test_parameter_fixes.py`

Demonstrates how to use parameter fixes for common issues and edge cases during conversion.

**Key features demonstrated:**
- Color profile handling
- Correction of problematic images
- Error recovery options
- Special case handling for unusual image types

**Usage:**
```bash
python test_parameter_fixes.py path/to/problematic_image.tif output_directory/
```

### `validate_jp2.py`

A utility script to validate JPEG2000 files against various standards and requirements.

**Key features demonstrated:**
- JPEG2000 validation using jpylyzer
- BnF compliance checking
- Metadata validation
- Structural integrity verification

**Usage:**
```bash
python validate_jp2.py path/to/image.jp2
```

## Running the Examples

All example scripts can be run directly from the command line. Most examples accept command-line arguments similar to the main JP2Forge CLI.

For detailed help on any example:

```bash
python example_name.py --help
```

## Integration Examples

These examples can be modified and integrated into your own workflows. The code demonstrates best practices for:

- Configuring JP2Forge programmatically
- Handling different image types
- Optimizing for performance and resource usage
- Implementing custom metadata handling

## Additional Notes

- All examples assume JP2Forge is properly installed and configured
- External dependencies (such as ExifTool and Kakadu, if used) should be installed separately
- Some examples may require specific input files to demonstrate their functionality correctly