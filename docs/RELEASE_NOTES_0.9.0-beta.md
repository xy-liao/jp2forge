# JP2Forge 0.9.0-beta (April 15, 2025)

We're excited to announce the first beta release of JP2Forge, a comprehensive solution for converting images to JPEG2000 format with support for both standard and BnF (Bibliothèque nationale de France) compliant workflows.

## Release Highlights

This beta release provides all core functionality for JPEG2000 conversion, quality analysis, and metadata handling:

- Full implementation of the BnF technical specifications for JPEG2000 files
- Comprehensive quality analysis with metrics (PSNR, SSIM, MSE)
- Detailed file size reporting for conversion evaluation
- Memory-efficient handling of large images
- Advanced parallel processing capabilities
- Flexible configuration system

## Installation

```bash
# Create and activate conda environment (recommended)
conda create -n jp2forge python=3.9
conda activate jp2forge

# Clone the repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Install dependencies
pip install -r requirements.txt

# Install ExifTool for metadata handling
# macOS: brew install exiftool
# Ubuntu/Debian: sudo apt install libimage-exiftool-perl
# Windows: Download from https://exiftool.org
```

## Key Features

### Multiple Compression Modes

- **lossless**: No data loss, larger file size
- **lossy**: Higher compression with data loss
- **supervised**: Quality-controlled compression with analysis
- **bnf_compliant**: BnF standards with fixed compression ratios

### Quality Analysis

- Objective quality metrics (PSNR, SSIM, MSE)
- Detailed reports for each converted image
- File size analysis with compression ratios
- Visual quality threshold enforcement

### Advanced Processing

- Parallel processing with automatic resource management
- Memory-efficient streaming for large images
- Adaptive chunking for memory-constrained environments

### BnF Compliance

- Fixed compression ratios by document type
- BnF-compliant XMP metadata in UUID box
- Required technical parameters implemented

## Usage Examples

### Basic Conversion

```bash
python -m cli.workflow input.tif output_dir/
```

### Batch Processing with BnF Compliance

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --recursive
```

### Parallel Processing with Reporting

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

## Known Limitations

As this is a beta release, please be aware of the following limitations:

1. Kakadu integration requires separate installation of Kakadu software
2. Some advanced JPEG2000 Part 2 features are not yet supported
3. Limited validation for uncommon color spaces
4. Report formatting options are currently fixed

## Feedback and Contributions

We welcome feedback on this beta release! Please report any issues or suggestions through:

- GitHub Issues: https://github.com/xy-liao/jp2forge/issues

## License

JP2Forge is released under the MIT License.

## Acknowledgements

Special thanks to:
- Bibliothèque nationale de France for publishing their technical specifications
- The digital preservation community for guidance and feedback
- Early testers who provided valuable input