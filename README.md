# JP2Forge

[![PyPI version](https://badge.fury.io/py/jp2forge.svg)](https://badge.fury.io/py/jp2forge) [![Version: 0.9.8](https://img.shields.io/badge/Version-0.9.8-blue.svg)](https://github.com/xy-liao/jp2forge/releases/tag/v0.9.8) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.11–3.12](https://img.shields.io/badge/python-3.11--3.12-blue.svg)](https://www.python.org/downloads/) [![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge) [![Security: SonarQube Compliant](https://img.shields.io/badge/Security-SonarQube%20Compliant-brightgreen.svg)](https://www.sonarsource.com/products/sonarqube/)

JP2Forge is a Python tool for JPEG2000 conversion built specifically for **cultural heritage digitization and archival workflows**. It targets institutions that must meet strict preservation standards — in particular, compliance with the **BnF (Bibliothèque nationale de France)** technical specifications for digital collections.

> **Not sure if JP2Forge is right for you?**
> If you need a quick one-off format conversion, a general-purpose tool like `magick input.tif output.jp2` or a lightweight library like [`glymur`](https://glymur.readthedocs.io/) will serve you better. JP2Forge is purpose-built for institutions where conversion quality must be mathematically verified, metadata chains of custody must be preserved, and thousands of high-resolution TIFFs must be processed reliably in batch.

**Key capabilities:**
- BnF-compliant JPEG2000 conversion with fixed compression ratios and XMP metadata in UUID box
- PSNR/SSIM quality validation — mathematical proof that conversions meet archival thresholds
- ExifTool-based metadata preservation across the full conversion pipeline
- Parallel batch processing for large-scale institutional digitization campaigns
- Multi-page TIFF support with automatic page extraction
- Supervised compression mode with automatic lossless fallback

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

# Install core dependencies
pip install -r requirements.txt

# Optional: Install benchmarking dependencies
pip install jp2forge[benchmarking]

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
- **Advanced Parallel Processing**: High-throughput persistent worker pool with resource monitoring
- **Chunked Decoding**: Large files are decoded incrementally in row chunks (note: encoding still assembles the full image in memory once)
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

**Completed (v0.9.6+):**
- Refactored codebase with eliminated code duplication
- Shared utility modules for better maintainability
- Enhanced error handling and progress tracking
- Automated pytest suite (quality metrics, lossless round-trips, BnF
  ratio targets, XMP embedding) run in CI
- Publication-ready codebase structure

**🔄 Ongoing Development:**
- Test coverage expansion
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
