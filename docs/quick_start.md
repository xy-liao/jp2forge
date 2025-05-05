# JP2Forge Quick Start Guide

Welcome to JP2Forge! This guide provides essential commands to get you started quickly.

> **For Complete Documentation**: This guide contains only basic commands and common options. For detailed instructions, installation options, and advanced features, please refer to the [User Guide](user_guide.md).

## Basic Installation

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install jpylyzer

# Install ExifTool (required for metadata operations)
# macOS:
brew install exiftool
# Linux:
# sudo apt-get install libimage-exiftool-perl
# Windows:
# Download from https://exiftool.org/ and follow installation instructions
```

> **Note**: For detailed installation instructions including conda setup, external dependencies, and system-specific requirements, see the [Installation section](user_guide.md#1-installation) in the User Guide.

## Basic Commands

### 1. Convert a Single File

```bash
python -m cli.workflow input.tif output_dir/
```

### 2. Process a Directory

```bash
python -m cli.workflow input_dir/ output_dir/
```

### 3. Use BnF Compliance Mode

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### 4. Enable Parallel Processing

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

## Common Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--document-type` | Set document type | `photograph` |
| `--compression-mode` | Set compression mode | `supervised` |
| `--recursive` | Process subdirectories | False |
| `--parallel` | Enable parallel processing | False |
| `--bnf-compliant` | Use BnF compliance mode | False |

> **Note**: For complete list of options and detailed parameters, see the [Command-Line Interface section](user_guide.md#3-command-line-interface) in the User Guide.

## Output Location

- Converted JP2 files: `output_dir/`
- Processing reports: `reports/`
- Quality metrics: `reports/metrics/`

## Next Steps

- [User Guide](user_guide.md): Comprehensive documentation of all features
- [BnF Compliance](NOTATION.md): Archival standards information
- [Troubleshooting](user_guide.md#11-troubleshooting): Solutions for common issues
- [Example Workflows](user_guide.md#13-examples): Common use case examples

## Verifying Your Installation

After installation, you can run the test script to verify that everything is working correctly:

```bash
# Make the test script executable
chmod +x test_jp2forge.sh

# Run the test script
./test_jp2forge.sh
```

This will test JP2Forge in three scenarios:
1. Processing a single image directly
2. Processing a single image from input_dir
3. Processing multiple images from input_dir

If all tests pass, your installation is working correctly.