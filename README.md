# JP2Forge

[![PyPI version](https://badge.fury.io/py/jp2forge.svg)](https://badge.fury.io/py/jp2forge) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.8–3.12](https://img.shields.io/badge/python-3.8--3.12-blue.svg)](https://www.python.org/downloads/) [![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge) [![Security: SonarQube Compliant](https://img.shields.io/badge/Security-SonarQube%20Compliant-brightgreen.svg)](https://www.sonarsource.com/products/sonarqube/)

> **Supported Python versions:** JP2Forge officially supports Python 3.8 through 3.12 (inclusive). Older versions are not guaranteed to work with all dependencies (e.g., matplotlib >=3.9).

JP2Forge is a comprehensive Python tool for converting images to JPEG2000 format with support for standard and BnF (Bibliothèque nationale de France) compliant workflows.

**Key capabilities:**
- High-quality JPEG2000 conversion with multiple compression modes
- BnF-compliant processing for cultural heritage digitization
- Parallel processing for efficient batch operations
- Quality analysis and validation with PSNR/SSIM metrics
- Multi-page TIFF support with automatic page extraction
- Comprehensive metadata preservation and XMP integration

## Quick Start

### Installation

#### Option 1: From Source (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes jpylyzer)
pip install -r requirements.txt

# Install ExifTool (required for metadata operations)
# macOS:
brew install exiftool
# Linux:
# sudo apt-get install libimage-exiftool-perl
# Windows:
# Download from https://exiftool.org/ and follow installation instructions
```

#### Option 2: Via pip (Recommended for Users)

```bash
pip install jp2forge
# Install ExifTool separately (see above)
```

### Basic Usage

```bash
# Convert a single file
python -m cli.workflow input.tif output_dir/

# Process a directory with parallel processing
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4

# BnF-compliant conversion
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### Verifying Your Installation

To verify that everything is set up correctly:

```bash
# Make the test script executable
chmod +x test_jp2forge.sh

# Run the test script
./test_jp2forge.sh
```

This test script validates JP2Forge by processing images in three different scenarios and checking the outputs.

## Key Features

- **Multiple Compression Modes**: Lossless, lossy, supervised, and BnF-compliant
- **BnF Standards Support**: Fixed ratios, standard parameters, XMP metadata in UUID box
- **Advanced Parallel Processing**: Adaptive worker pool with resource monitoring
- **Memory-Efficient Processing**: Handles large files via streaming and chunking
- **Multi-page Document Support**: Automatic handling of multi-page TIFF files
- **Quality Analysis**: PSNR, SSIM, and MSE measurements

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/user_guide.md) | Comprehensive guide for end users |
| [CLI Reference](docs/cli_reference.md) | Complete command-line interface reference |
| [Developer Guide](docs/developer_guide.md) | Information for developers and contributors |
| [API Reference](docs/api_reference.md) | Core classes and functions reference |
| [BnF Compliance](docs/bnf_compliance.md) | Details about BnF compliance features |
| [Examples](examples/README.md) | Code examples for API usage |

## Command Reference

### Document Types

```bash
python -m cli.workflow input_dir/ output_dir/ --document-type photograph
```

- `photograph`: Standard photographic images (default)
- `heritage_document`: Historical documents with high-quality settings
- `color`: General color images
- `grayscale`: Grayscale images

### Compression Modes

```bash
python -m cli.workflow input_dir/ output_dir/ --compression-mode supervised
```

- `supervised`: Quality-controlled compression (default)
- `lossless`: No data loss
- `lossy`: Higher compression with data loss
- `bnf_compliant`: BnF standards with fixed ratios

### BnF Mode

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --metadata bnf_metadata.json
```

## Common Options

For a complete list of all options, see the [CLI Reference](docs/cli_reference.md).

| Option | Description |
|--------|-------------|
| `--parallel` | Enable parallel processing |
| `--max-workers N` | Set number of worker threads |
| `--memory-limit MB` | Set memory limit for large files |
| `--verbose` | Enable detailed logging |
| `--log-file PATH` | Save logs to file |
| `--config PATH` | Use configuration file |
| `--full-report` | Generate detailed reports with quality metrics |

## Current Status and Roadmap

JP2Forge is production-ready with comprehensive JPEG2000 conversion capabilities. Recent improvements include:

**✅ Completed (v0.9.6+):**
- Refactored codebase with eliminated code duplication
- Shared utility modules for better maintainability
- Enhanced error handling and progress tracking
- Comprehensive testing infrastructure
- Publication-ready codebase structure

**🔄 Ongoing Development:**
- Comprehensive unit test coverage expansion
- Performance optimization for large datasets
- Docker containerization support
- Extended BnF validation features

## Troubleshooting

See the [Troubleshooting Guide](docs/user_guide.md#11-troubleshooting) for common issues and solutions.


## License

JP2Forge is released under the MIT License.

## Related Project

- **[JP2Forge Web](https://github.com/xy-liao/jp2forge_web)**: A web interface for the JP2Forge JPEG2000 conversion library.

## Use Cases

JP2Forge is designed for:
- **Cultural Heritage Institutions**: Museums, libraries, and archives digitizing collections
- **Academic Research**: Digital humanities projects requiring high-quality image preservation
- **BnF Compliance**: Organizations following Bibliothèque nationale de France standards
- **Batch Processing**: Efficient conversion of large image datasets
- **Quality Control**: Projects requiring rigorous quality analysis and validation

## Acknowledgments

This project follows technical requirements described in BnF reference documents:
- BnF Referential (2015): [PDF](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)
- BnF Documentation (2021): [PDF](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

JP2Forge serves the digital humanities community and cultural heritage institutions worldwide.
