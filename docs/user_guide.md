# JP2Forge User Guide

This guide provides comprehensive instructions for using JP2Forge to convert images to JPEG2000 format with various options and configurations.

## Table of Contents

1. [Installation](#1-installation)
2. [Basic Usage](#2-basic-usage)
3. [Compression Modes](#3-compression-modes)
4. [Document Types](#4-document-types)
5. [BnF Compliance](#5-bnf-compliance)
6. [Parallel Processing](#6-parallel-processing)
7. [Large Image Handling](#7-large-image-handling)
8. [Multi-page TIFF Processing](#8-multi-page-tiff-processing)
9. [Metadata Management](#9-metadata-management)
10. [Configuration](#10-configuration)
11. [Troubleshooting](#11-troubleshooting)

## 1. Installation

> **Supported Python versions:** JP2Forge officially supports Python 3.8 through 3.12 (inclusive).

### System Requirements

- Python 3.8, 3.9, 3.10, 3.11, or 3.12
- 4GB RAM minimum (8GB+ recommended for large images)
- External dependencies:
  - ExifTool (required for metadata handling)

### Installing JP2Forge

#### Using Python venv (Recommended)

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Using Conda

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate conda environment
conda create -n jp2forge python=3.9
conda activate jp2forge

# Install dependencies
conda install -c conda-forge pillow numpy psutil exiftool lxml pyyaml
pip install jpylyzer structlog
```

### Installing External Tools

#### ExifTool (Required)

- **macOS**: `brew install exiftool`
- **Ubuntu/Debian**: `sudo apt install libimage-exiftool-perl`
- **Windows**: Download from [ExifTool's website](https://exiftool.org)


## 2. Basic Usage

### Convert a Single Image

```bash
python -m cli.workflow input.tif output_dir/
```

### Process All Images in a Directory

```bash
python -m cli.workflow input_dir/ output_dir/ --recursive
```

### Enable Parallel Processing

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

### Common Options

```bash
# Specify compression mode
python -m cli.workflow input.tif output_dir/ --compression-mode lossy

# Set document type
python -m cli.workflow input.tif output_dir/ --document-type photograph

# Enable verbose logging
python -m cli.workflow input.tif output_dir/ --verbose
```

## 3. Compression Modes

### Supervised Mode (Default)

Quality-controlled compression that analyzes results:

```bash
python -m cli.workflow input.tif output_dir/ --compression-mode supervised
```

### Lossy Mode

Higher compression with some quality loss:

```bash
python -m cli.workflow input.tif output_dir/ --compression-mode lossy
```

### Lossless Mode

No quality loss, but larger file size:

```bash
python -m cli.workflow input.tif output_dir/ --compression-mode lossless
```

### BnF Compliant Mode

Follows Bibliothèque nationale de France standards:

```bash
python -m cli.workflow input.tif output_dir/ --compression-mode bnf_compliant
```

## 4. Document Types

### Photograph (Default)

For photographic images:

```bash
python -m cli.workflow input.tif output_dir/ --document-type photograph
```

### Heritage Document

For historical documents with high detail:

```bash
python -m cli.workflow input.tif output_dir/ --document-type heritage_document
```

### Color

For general color documents:

```bash
python -m cli.workflow input.tif output_dir/ --document-type color
```

### Grayscale

For grayscale documents:

```bash
python -m cli.workflow input.tif output_dir/ --document-type grayscale
```

## 5. BnF Compliance

### Enabling BnF Mode

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### BnF Document Types and Compression Ratios

| Document Type | Compression Ratio | Command |
|---------------|-------------------|---------|
| Photograph | 1:4 | `--document-type photograph` |
| Heritage Document | 1:4 | `--document-type heritage_document` |
| Color | 1:6 | `--document-type color` |
| Grayscale | 1:16 | `--document-type grayscale` |


### Compression Ratio Tolerance

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --compression-ratio-tolerance 0.03  # 3% tolerance
```

## 6. Parallel Processing

### Basic Parallel Processing

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --max-workers 4
```

### Adaptive Worker Pool

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --min-workers 2 \
  --max-workers 8
```

### Resource Thresholds

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --memory-threshold 0.8 \
  --cpu-threshold 0.9
```

## 7. Large Image Handling

### Memory-Efficient Processing

```bash
python -m cli.workflow large_image.tif output_dir/ \
  --memory-limit 2048  # Limit to 2GB
```

### Force Chunked Processing

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --force-chunking
```

### Chunk Size Configuration

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --chunk-size 500000
```

## 8. Multi-page TIFF Processing

### Basic Multi-page Handling

JP2Forge automatically detects and processes multi-page TIFF files:

```bash
python -m cli.workflow multipage.tif output_dir/
```

Each page is saved as a separate JP2 file: `filename_page_0.jp2`, `filename_page_1.jp2`, etc.

### Memory Optimization

```bash
python -m cli.workflow multipage.tif output_dir/ \
  --memory-limit-mb 2048 \
  --chunk-size 500000
```

### Handling Existing Files

```bash
# Skip existing files
python -m cli.workflow multipage.tif output_dir/ --skip-existing

# Overwrite existing files
python -m cli.workflow multipage.tif output_dir/ --overwrite
```

## 9. Metadata Management

### Basic Metadata

```bash
python -m cli.workflow input.tif output_dir/ \
  --metadata-creator "JP2Forge User" \
  --metadata-description "Sample conversion"
```

### Using Metadata Files

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --metadata-file metadata.json
```

Example `metadata.json`:

```json
{
  "xmp:CreatorTool": "JP2Forge 2.0",
  "xmp:CreateDate": "2023-05-25T12:00:00Z",
  "dc:creator": "JP2Forge User",
  "dc:description": "Sample image conversion"
}
```

### BnF Metadata

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --metadata-file bnf_metadata.json
```

Example `bnf_metadata.json`:

```json
{
  "dcterms:isPartOf": "NUM_123456",
  "dcterms:provenance": "Bibliothèque nationale de France",
  "dc:relation": "ark:/12148/cb123456789",
  "dc:source": "FOL-Z-123",
  "tiff:Model": "Phase One P45+",
  "tiff:Make": "Phase One",
  "aux:SerialNumber": "1234567890",
  "xmp:CreatorTool": "JP2Forge 2.0",
  "tiff:Artist": "Image Digitization Operator"
}
```

## 10. Configuration

### Command-Line Configuration

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossy \
  --quality 50 \
  --parallel \
  --max-workers 8
```

### Configuration Files

Save configuration:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossy \
  --save-config my_config.yaml
```

Use saved configuration:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --config my_config.yaml
```

### Environment Variables

```bash
export JP2FORGE_COMPRESSION_MODE=lossy
export JP2FORGE_QUALITY=50
export JP2FORGE_PARALLEL=true
export JP2FORGE_MAX_WORKERS=8

python -m cli.workflow input_dir/ output_dir/
```

## 11. Troubleshooting

### Memory Issues

For large images:

```bash
python -m cli.workflow large_image.tif output_dir/ \
  --memory-limit 2048 \
  --chunk-size 250000
```

### Metadata Errors

If metadata operations fail:

```bash
python -m cli.workflow input.tif output_dir/ \
  --exiftool-path /path/to/exiftool
```

### Slow Processing

For improved performance:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --max-workers 8
```

### Logging

Enable detailed logging:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --verbose \
  --log-file conversion.log
```

### Common Error Messages

| Error Message | Solution |
|---------------|----------|
| "ExifTool not found" | Install ExifTool or use `--exiftool-path` |
| "Memory error during processing" | Use `--memory-limit` and `--chunk-size` |
| "Invalid metadata format" | Validate JSON syntax and required fields |
| "Compression ratio outside tolerance" | Adjust `--compression-ratio-tolerance` |

### Help Command

For complete option list:

```bash
python -m cli.workflow --help
```
