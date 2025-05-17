# JP2Forge User Guide

This guide provides comprehensive instructions for using JP2Forge to convert images to JPEG2000 format with various options and configurations.

## Table of Contents

1. [Installation](#1-installation)
2. [Quick Start](#2-quick-start)
3. [Command-Line Interface](#3-command-line-interface)
4. [Configuration Options](#4-configuration-options)
5. [Processing Modes](#5-processing-modes)
6. [BnF Compliance](#6-bnf-compliance)
7. [Metadata Management](#7-metadata-management)
8. [Parallel Processing](#8-parallel-processing)
9. [Large Image Handling](#9-large-image-handling)
10. [Multi-page TIFF Processing](#10-multi-page-tiff-processing)
11. [Troubleshooting](#11-troubleshooting)
12. [Advanced Usage](#12-advanced-usage)
13. [Examples](#13-examples)
14. [Technical Reference](#14-technical-reference)
15. [Release Notes](#15-release-notes)
16. [Web Interface](#16-web-interface)

## 1. Installation

### 1.1 System Requirements

- Python 3.9 or newer
- 4GB RAM minimum (8GB+ recommended for large images)
- External dependencies:
  - ExifTool (required for metadata handling)
  - Kakadu (optional, for BnF-compliant compression)

### 1.2 Installing JP2Forge

#### Using Python venv (Recommended for Most Users)

Python's built-in virtual environment tool is lightweight and perfect for most use cases:

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Advantages of venv:**
- Built into Python, no additional installation required
- Lightweight and simple to use
- Perfect for development and most production uses
- Isolates project dependencies from system Python

#### Using Conda (Recommended for Complex Environments)

Conda is excellent for managing complex dependencies, especially when you need specific versions of scientific libraries:

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

**Advantages of conda:**
- Better handling of complex binary dependencies
- Often easier to install packages with C extensions
- Can manage both Python and non-Python dependencies
- Useful for environments with specific version requirements

#### Standard Installation

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Install Python dependencies
pip install -r requirements.txt
```

### 1.3 Installing External Tools

#### ExifTool

ExifTool is required for metadata functionality:

- **macOS**: `brew install exiftool`
- **Ubuntu/Debian**: `sudo apt install libimage-exiftool-perl`
- **Windows**: Download from [ExifTool's website](https://exiftool.org)

#### Kakadu (Optional)

For BnF-compliant processing, Kakadu Software is recommended:

- Kakadu is a commercial software that requires separate licensing
- Download from [Kakadu Software](http://kakadusoftware.com/)
- Install according to the provided instructions
- Set the path to the Kakadu executable using the `--kakadu-path` option

## 2. Quick Start

### 2.1 Basic Usage

Convert a single image:

```bash
python -m cli.workflow input.tif output_dir/
```

Process all images in a directory:

```bash
python -m cli.workflow input_dir/ output_dir/ --recursive
```

### 2.2 Common Options

Specify compression mode:

```bash
python -m cli.workflow input.tif output_dir/ --compression-mode lossy
```

Set document type:

```bash
python -m cli.workflow input.tif output_dir/ --document-type photograph
```

Enable parallel processing:

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

### 2.3 BnF Mode

Process files according to BnF standards:

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

## 3. Command-Line Interface

### 3.1 Basic Syntax

```
python -m cli.workflow <input_path> <output_directory> [options]
```

Where:
- `<input_path>`: Path to an image file or directory
- `<output_directory>`: Directory where converted images will be saved

> **Note**: For a comprehensive list of all available arguments, see the [CLI Reference](cli_reference.md) document.

### 3.2 Common Options

Below are the most frequently used options. For a complete reference of all available options, see the [CLI Reference](cli_reference.md).

| Option | Description | Default |
|--------|-------------|---------|
| `--recursive` | Process subdirectories recursively | False |
| `--parallel` | Enable parallel processing | False |
| `--compression-mode` | Compression mode (`lossless`, `lossy`, `supervised`, `bnf_compliant`) | `supervised` |
| `--document-type` | Document type (`photograph`, `heritage_document`, `color`, `grayscale`) | `photograph` |
| `--quality` | Quality level (0-100) for lossy compression | 40.0 |
| `--verbose` | Enable verbose output | False |
| `--log-file` | Path to log file | None |

### 3.3 Help Command

To display all available options:

```bash
python -m cli.workflow --help
```

### 3.4 Custom Directory Paths

JP2Forge supports fully customizable input, output, and report directories:

#### Basic Directory Customization

```bash
# Process images from a custom input directory to a custom output directory
python -m cli.workflow /path/to/my/images/ /path/to/my/jp2_files/
```

#### Custom Report Directory

By default, reports are saved to the "reports" directory. Use `--report-dir` to specify a custom location:

```bash
python -m cli.workflow /path/to/my/images/ /path/to/my/jp2_files/ \
  --report-dir /path/to/my/reports/
```

#### Directory Organization Best Practices

For large projects or multiple datasets, consider organizing your directories by project:

```bash
project_a/
  ├── input/
  ├── output_dir/
  └── reports/

project_b/
  ├── input/
  ├── output_dir/
  └── reports/
```

#### Verification

After processing completes, JP2Forge will show the paths where files were saved:
- Converted images: in the specified output directory
- Reports: in the specified report directory
- Validation results: in the report directory

You can verify that custom directories are being used by checking the report files generated, which will include the paths used in the processing configuration.

## 4. Configuration Options

### 4.1 Command-Line Configuration

The most direct way to configure JP2Forge is through command-line options:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossy \
  --quality 50 \
  --parallel \
  --max-workers 8
```

### 4.2 Configuration Files

Save current configuration to a file:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossy \
  --save-config my_config.yaml
```

Use a saved configuration:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --config my_config.yaml
```

### 4.3 Environment Variables

All configuration options can be set via environment variables with the `JP2FORGE_` prefix:

```bash
# Set configuration via environment variables
export JP2FORGE_COMPRESSION_MODE=lossy
export JP2FORGE_QUALITY=50
export JP2FORGE_PARALLEL=true
export JP2FORGE_MAX_WORKERS=8

# Run with environment configuration
python -m cli.workflow input_dir/ output_dir/
```

### 4.4 Configuration Precedence

Configuration options are applied in the following order of precedence (highest to lowest):

1. Command-line arguments
2. Configuration file (if specified with `--config`)
3. Environment variables
4. Default values

## 5. Processing Modes

JP2Forge supports several processing modes to meet different requirements:

### 5.1 Standard Mode

Default processing mode that balances quality and file size:

```bash
python -m cli.workflow input.tif output_dir/
```

### 5.2 Compression Modes

JP2Forge offers several compression modes to meet different needs:

#### 5.2.1 Supervised Mode (Default)

Quality-controlled compression that analyzes results:

```bash
python -m cli.workflow input.tif output_dir/ \
  --compression-mode supervised \
  --quality-threshold 40.0
```

In supervised mode, JP2Forge analyzes the compressed image quality and can fallback to lossless compression if quality requirements aren't met.

#### 5.2.2 Lossy Mode

Higher compression with some quality loss:

```bash
python -m cli.workflow input.tif output_dir/ \
  --compression-mode lossy \
  --quality 50
```

Lossy mode prioritizes smaller file sizes at the expense of some image quality. The quality parameter controls the balance between size and quality.

#### 5.2.3 Lossless Mode

No quality loss, but larger file size:

```bash
python -m cli.workflow input.tif output_dir/ \
  --compression-mode lossless
```

Lossless mode guarantees that no image information is lost during compression, but results in larger files.

#### 5.2.4 BnF Compliant Mode

Follows Bibliothèque nationale de France standards:

```bash
python -m cli.workflow input.tif output_dir/ \
  --compression-mode bnf_compliant
```

This mode applies fixed compression ratios and parameters according to BnF specifications. See section 6 for more details on BnF compliance.

### 5.3 Document Types

Select the appropriate document type for optimal results. Document types influence compression parameters, especially in BnF compliant mode.

#### 5.3.1 Photograph

For photographic images (default):

```bash
python -m cli.workflow input.tif output_dir/ \
  --document-type photograph
```

In BnF compliant mode, photographs use a 1:4 compression ratio (4:1 in JP2Forge notation).

#### 5.3.2 Heritage Document

For historical documents with high detail:

```bash
python -m cli.workflow input.tif output_dir/ \
  --document-type heritage_document
```

In BnF compliant mode, heritage documents use a 1:4 compression ratio (4:1 in JP2Forge notation).

#### 5.3.3 Color

For general color documents:

```bash
python -m cli.workflow input.tif output_dir/ \
  --document-type color
```

In BnF compliant mode, color documents use a 1:6 compression ratio (6:1 in JP2Forge notation).

#### 5.3.4 Grayscale

For grayscale documents:

```bash
python -m cli.workflow input.tif output_dir/ \
  --document-type grayscale
```

In BnF compliant mode, grayscale documents use a 1:16 compression ratio (16:1 in JP2Forge notation).

## 6. BnF Compliance

JP2Forge provides specialized support for BnF (Bibliothèque nationale de France) compliance:

### 6.1 Enabling BnF Mode

Process files according to BnF standards:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant
```

### 6.2 BnF Document Types and Ratios

> **Note on Compression Ratio Notation**: BnF documentation uses different notation than JP2Forge. See [Notation Conventions](NOTATION.md) for a detailed explanation.

BnF mode uses fixed compression ratios based on document types:

| Document Type | Compression Ratio | Option |
|---------------|-------------------|--------|
| Photograph | 1:4 | `--document-type photograph` |
| Heritage Document | 1:4 | `--document-type heritage_document` |
| Color | 1:6 | `--document-type color` |
| Grayscale | 1:16 | `--document-type grayscale` |

Example:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --document-type color  # Uses 1:6 ratio
```

### 6.3 Compression Ratio Tolerance

BnF mode includes a tolerance for compression ratios:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --compression-ratio-tolerance 0.03  # 3% tolerance
```

Default tolerance is 5% (0.05).

### 6.4 Using Kakadu for BnF Compliance

For strict BnF compliance, using Kakadu is recommended:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --use-kakadu \
  --kakadu-path /path/to/kdu_compress
```

## 7. Metadata Management

JP2Forge provides comprehensive metadata handling capabilities:

### 7.1 Basic Metadata

Add basic metadata to output files:

```bash
python -m cli.workflow input.tif output_dir/ \
  --metadata-creator "JP2Forge User" \
  --metadata-description "Sample image conversion"
```

### 7.2 Using Metadata Files

Use a JSON file for more complex metadata:

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

### 7.3 BnF Metadata

For BnF-compliant metadata:

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

### 7.4 Metadata Validation

Validate BnF metadata compliance:

```bash
python -m cli.workflow --validate-metadata bnf_metadata.json
```

## 8. Parallel Processing

JP2Forge includes advanced parallel processing capabilities for improved performance:

### 8.1 Basic Parallel Processing

Enable parallel processing with a fixed number of workers:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --max-workers 4
```

### 8.2 Adaptive Worker Pool

Use adaptive workers that adjust based on system resources:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --min-workers 2 \
  --max-workers 8
```

### 8.3 Resource Thresholds

Configure resource thresholds for adaptive scaling:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --memory-threshold 0.8  # Scale down if memory usage > 80%
  --cpu-threshold 0.9     # Scale down if CPU usage > 90%
```

### 8.4 Progress Reporting

Enable progress reporting for parallel processing:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --show-progress
```

## 9. Large Image Handling

JP2Forge includes specialized support for processing very large images:

### 9.1 Memory-Efficient Processing

Limit memory usage for large images:

```bash
python -m cli.workflow large_image.tif output_dir/ \
  --memory-limit 2048  # Limit to 2GB
```

### 9.2 Chunked Processing

Force chunked processing for all images:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --force-chunking
```

### 9.3 Chunk Size Configuration

Configure minimum chunk height for processing:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --min-chunk-height 32
```

### 9.4 Memory Mapping

Enable memory mapping for efficient file access:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --use-memory-mapping
```

## 10. Multi-page TIFF Processing

JP2Forge supports processing multi-page TIFF files, enabling conversion of each page into separate JPEG2000 files.

### 10.1 Basic Multi-page TIFF Handling

When JP2Forge detects a multi-page TIFF file, it automatically processes each page separately and generates individual JP2 files for each page:

```bash
python -m cli.workflow multipage.tif output_dir/
```

Each page will be extracted and saved as a separate JPEG2000 file in the output directory with automatic naming: `filename_page_0.jp2`, `filename_page_1.jp2`, etc.

### 10.2 Handling Existing Files

Control how JP2Forge handles existing files when processing multi-page TIFFs:

```bash
# Skip files that already exist in the output directory
python -m cli.workflow multipage.tif output_dir/ --skip-existing

# Overwrite files that already exist
python -m cli.workflow multipage.tif output_dir/ --overwrite
```

### 10.3 Metadata for Multi-page TIFFs

Metadata can be applied to each page separately, with automatic page number annotation:

```bash
python -m cli.workflow multipage.tif output_dir/ --metadata-file metadata.json
```

The page number will be added to the metadata as `tiff:PageNumber` in the format `page/total` (e.g., "2/15").

### 10.4 Memory Optimization for Large Multi-page TIFFs

For large multi-page TIFFs, memory optimization is essential. JP2Forge provides two key parameters to control memory usage during processing:

```bash
python -m cli.workflow multipage.tif output_dir/ \
  --memory-limit-mb 2048 \
  --chunk-size 500000
```

#### 10.4.1 Memory Limit Parameter

The `--memory-limit-mb` parameter sets a target memory limit in megabytes. When processing large multi-page TIFFs:

- If the estimated memory usage for processing a page exceeds this limit, JP2Forge automatically switches to memory-efficient processing mode
- Default: 4096 MB (4 GB)
- Recommended: Set to 50-75% of your available system RAM

```bash
python -m cli.workflow multipage.tif output_dir/ --memory-limit-mb 1536
```

#### 10.4.2 Chunk Size Parameter

The `--chunk-size` parameter controls the size of image chunks processed at once:

- Lower values reduce memory usage but may slightly increase processing time
- Default: 1,000,000 pixels
- Values below 1,000,000 will trigger memory-efficient processing
- Recommended range: 250,000-500,000 for memory-constrained environments

```bash
python -m cli.workflow multipage.tif output_dir/ --chunk-size 250000
```

#### 10.4.3 Combined Parameter Usage

For optimal memory usage control, you can use both parameters together:

```bash
python -m cli.workflow multipage.tif output_dir/ \
  --memory-limit-mb 1024 \
  --chunk-size 300000
```

This configuration will ensure JP2Forge stays within memory constraints while processing large multi-page TIFFs.

#### 10.4.4 Identifying Memory-Efficient Processing

When memory-efficient processing is triggered, you'll see a log message like:

```
Using memory-efficient processing for page X with chunk_size=Y, memory_limit_mb=Z
```

This indicates that JP2Forge is using a streaming approach to process the image in chunks, minimizing memory usage.

### 10.5 Combining with Other Options

Multi-page TIFF handling works with all other JP2Forge features:

```bash
# Process in BnF-compliant mode
python -m cli.workflow multipage.tif output_dir/ --bnf-compliant

# With lossless compression
python -m cli.workflow multipage.tif output_dir/ --compression-mode lossless

# With quality control and advanced settings
python -m cli.workflow multipage.tif output_dir/ \
  --compression-mode supervised \
  --quality-threshold 42 \
  --num-resolution-levels 8
```

## 11. Troubleshooting

### 11.1 Common Issues

#### Memory Issues

If you encounter memory errors with large images:

```bash
python -m cli.workflow large_image.tif output_dir/ \
  --memory-limit 2048 \
  --min-chunk-height 32
```

#### Metadata Errors

If metadata operations fail:

```bash
python -m cli.workflow input.tif output_dir/ \
  --exiftool-path /path/to/exiftool
```

#### Slow Processing

If processing is slow:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --adaptive-workers \
  --max-workers 8
```

### 11.2 Logging

Enable detailed logging for troubleshooting:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --verbose \
  --log-file conversion.log
```

### 11.3 Configuration Problems

If configuration isn't being applied correctly:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --debug \
  --show-config
```

### 11.4 Common Error Messages

| Error Message | Possible Cause | Solution |
|---------------|----------------|----------|
| "ExifTool not found" | ExifTool not installed or not in PATH | Install ExifTool or specify path with `--exiftool-path` |
| "Memory error during processing" | Image too large for available memory | Use `--memory-limit` and `--force-chunking` |
| "Invalid metadata format" | Metadata JSON file improperly formatted | Validate JSON syntax and required fields |
| "Compression ratio outside tolerance" | BnF ratio requirements not met | Adjust `--compression-ratio-tolerance` or check image content |

## 12. Advanced Usage

### 12.1 Color Profile Management

Preserve color profiles:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --preserve-icc-profiles
```

Specify default color profiles:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --default-rgb-profile /path/to/srgb.icc
```

### 12.2 Advanced JPEG2000 Parameters

Set specific JPEG2000 parameters:

```bash
python -m cli.workflow input.tif output_dir/ \
  --num-resolution-levels 8 \
  --quality-layers 12 \
  --progression-order RPCL \
  --tile-size 1024x1024 \
  --code-block-size 64x64
```

### 12.3 Custom External Tools

Use custom external tool paths:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --use-kakadu \
  --kakadu-path /custom/path/to/kdu_compress \
  --exiftool-path /custom/path/to/exiftool
```

### 12.4 API Integration

For programmatic use, import JP2Forge modules:

```python
from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

# Create configuration
config = WorkflowConfig(
    output_dir="output_dir/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED
)

# Create workflow
workflow = StandardWorkflow(config)

# Process a file
result = workflow.process_file("input.tif")
```

## 13. Examples

### 13.1 Basic Conversion

Convert a single TIFF to JPEG2000:

```bash
python -m cli.workflow input.tif output_dir/
```

### 13.2 Batch Processing with Parallel Execution

Process a directory of images in parallel:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --recursive \
  --parallel \
  --adaptive-workers \
  --max-workers 8 \
  --show-progress
```

### 13.3 BnF-Compliant Conversion

Convert images according to BnF standards:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --bnf-compliant \
  --document-type heritage_document \
  --use-kakadu \
  --metadata-file bnf_metadata.json
```

### 13.4 High-Quality Archival Conversion

Convert images for archival purposes:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossless \
  --preserve-icc-profiles \
  --num-resolution-levels 12
```

### 13.5 Fast Web-Optimized Conversion

Convert images for web use:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --compression-mode lossy \
  --quality 30 \
  --num-resolution-levels 6 \
  --parallel
```

## 14. Technical Reference

### 14.1 BnF JPEG2000 Parameters

When using `--bnf-compliant`, the following parameters are applied:

- **Compression**: Irreversible (9-7 floating transform, ICT)
- **Compression Ratios**:
  - Specialized documents: 1:4
  - Exceptional documents: 1:4
  - Standard printed documents: 1:6
  - Grayscale transparent documents: 1:16
- **Tolerance**: 5% (configurable)
- **Fallback**: Lossless compression (5-3 integer transform, RCT) for files outside tolerance
- **Resolution Levels**: 10
- **Quality Levels**: 10
- **Progression Order**: RPCL (Resolution-Position-Component-Layer)
- **Robustness Markers**: SOP, EPH, PLT
- **Code Block Size**: 64x64
- **Tile Size**: 1024x1024
- **Precinct Size**: {256,256},{256,256},{128,128}

### 14.2 BnF Metadata Structure

Required XMP metadata in UUID box:

- `dcterms:isPartOf`: Document identifier (e.g., "NUM_123456")
- `dcterms:provenance`: Document owner (e.g., "Bibliothèque nationale de France")
- `dc:relation`: ARK identifier (e.g., "ark:/12148/cb123456789")
- `dc:source`: Original document call number (e.g., "FOL-Z-123")
- `tiff:Model`: Device model used for digitization
- `tiff:Make`: Device manufacturer
- `aux:SerialNumber`: Device serial number
- `xmp:CreatorTool`: Software used for creation
- `xmp:CreateDate`: Creation date (ISO-8601 format)
- `xmp:ModifyDate`: Last modification date (ISO-8601 format)
- `tiff:Artist`: Digitization operator or organization

### 14.3 Quality Metrics

JP2Forge calculates several quality metrics:

- **PSNR**: Peak Signal-to-Noise Ratio (higher is better)
  - > 40 dB: Excellent quality
  - 30-40 dB: Good quality
  - < 30 dB: Medium to low quality

- **SSIM**: Structural Similarity Index (higher is better)
  - > 0.95: Excellent structural preservation
  - 0.90-0.95: Good structural preservation
  - < 0.90: More significant structural changes

- **MSE**: Mean Square Error (lower is better)

### 14.4 Status Codes

Processing results include status codes:

- **SUCCESS**: Successfully processed with all quality metrics above thresholds
- **WARNING**: Processed but quality metrics below thresholds
- **FAILURE**: Processing failed, no output file generated
- **SKIPPED**: File ignored (invalid image or corrupted)

## 15. Release Notes

JP2Forge maintains detailed release notes for each version, documenting all changes, improvements, and fixes. For the complete release history, please refer to:

- [JP2Forge Changelog](../CHANGELOG.md)

See the changelog for information about the latest release, including new features, improvements, and bug fixes.

## 16. Web Interface

For a web-based interface to JP2Forge, check out [JP2Forge Web](https://github.com/xy-liao/jp2forge_web). This is a case study implementation that showcases selected functionality of the more comprehensive JP2Forge tool.
