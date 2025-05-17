# JP2Forge

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge) [![Version: 0.9.6](https://img.shields.io/badge/Version-0.9.6-blue.svg)](https://github.com/xy-liao/jp2forge/releases/tag/v0.9.6)

**Current Status: Release** - JP2Forge 0.9.6 is now available! This version fixes report generation issues in all processing modes and adds comprehensive testing capabilities. See the [CHANGELOG](CHANGELOG.md) for details.

JP2Forge converts images to JPEG2000 format with support for standard and BnF (Bibliothèque nationale de France) compliant workflows.

## Current Status and Roadmap

JP2Forge is currently at version 0.9.6 with functional BnF-compliant JPEG2000 conversion capabilities. We have identified several areas for improvement which are documented in our [Implementation Roadmap](docs/implementation_roadmap.md).

Key planned enhancements for upcoming versions include:
- Automatic BnF validation integration
- UUID collision detection
- Comprehensive unit test infrastructure
- Improved architecture with factory patterns
- Enhanced documentation

See the [Implementation Roadmap](docs/implementation_roadmap.md) for the complete list of planned improvements and their target versions.

## What's New (May 2025)

- **🛠️ Improved Documentation**: Streamlined documentation with new [Quick Start Guide](docs/quick_start.md)
- **🐛 Bug Fixes**: Fixed report generation issues in all processing modes
- **🧪 Testing**: Added comprehensive test script for validating JP2 conversion
- **💾 Memory Optimizations**: Enhanced chunking mechanism for large TIFF processing
- **📊 Performance**: Fixed memory-efficient processing trigger logic

[View all changes →](CHANGELOG.md)

## Quick Start

### Installation

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

### Basic Usage

```bash
# Convert a single file
python -m cli.workflow input.tif output_dir/

# Process a directory with parallel processing
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4

# BnF-compliant conversion
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

For a comprehensive reference of all available command-line options, see the [CLI Reference](docs/cli_reference.md).

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
| [Architecture](docs/architecture.md) | System architecture and design |
| [BnF Compliance](docs/NOTATION.md) | Details about BnF compliance features |
| [API Examples](examples/README.md) | Code examples for API usage |
| [Release Notes](docs/releases/index.md) | Version history and changes |

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

## Troubleshooting

See the [Troubleshooting Guide](docs/user_guide.md#11-troubleshooting) for common issues and solutions.

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

JP2Forge is released under the MIT License.

## Acknowledgments

This project follows technical requirements described in BnF reference documents:
- BnF Referential (2015): [PDF](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)
- BnF Documentation (2021): [PDF](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)
