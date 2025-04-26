# JP2Forge: JPEG2000 Processing Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge) [![Version: 0.9.1](https://img.shields.io/badge/Version-0.9.1-blue.svg)](https://github.com/xy-liao/jp2forge/releases/tag/v0.9.1)

**Current Status: Release** - JP2Forge 0.9.1 is now available! See the [Release Notes](docs/RELEASE_NOTES_0.9.1.md) for details.

JP2Forge is a comprehensive solution for converting images to JPEG2000 format with support for both standard and BnF (Bibliothèque nationale de France) compliant workflows. This project implements JPEG2000 processing according to technical specifications published by the Bibliothèque nationale de France (BnF) in their "Référentiel de format de fichier image v2" (2015). This implementation is provided for educational and training purposes to demonstrate standards implementation. All BnF-specific parameters are based on publicly available technical documentation with proper attribution to BnF as the source of these specifications.

## Recent Updates

- Added advanced parallel processing with adaptive worker scaling
- Implemented memory-efficient streaming image processor for large files
- Added proper XML processing for metadata with lxml
- Created centralized configuration system with validation
- Enhanced external tool management with automatic detection
- Added support for large image processing via chunking
- Improved color profile handling for unusual color spaces
- Enhanced error recovery and robustness
- Refactored metadata handling for better organization and extensibility
- Added configurable logging with file output option
- See the [CHANGELOG](CHANGELOG.md) for a full list of changes

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [BnF Compliance](#bnf-compliance)
6. [Mode Switching](#mode-switching)
7. [Result Interpretation](#result-interpretation)
8. [Advanced Configuration](#advanced-configuration)
9. [API Usage](#api-usage)
10. [Troubleshooting](#troubleshooting)
11. [Intellectual Property](#intellectual-property)
12. [Project Architecture](#project-architecture)

## Overview

JP2Forge provides tools for:
- Converting standard image formats to JPEG2000
- Quality analysis with pixel loss assessment
- Metadata handling with BnF compliant format support
- Parallel processing for improved performance
- Configurable workflows and compression modes

## Features

- **Multiple Compression Modes**:
  - `lossless`: No data loss, larger file size
  - `lossy`: Higher compression with data loss
  - `supervised`: Quality-controlled compression with analysis
  - `bnf_compliant`: BnF standards with fixed compression ratios

- **BnF Standards Support**:
  - Fixed compression ratios by document type
  - Standard technical parameters (resolution levels, progression order)
  - XMP metadata in UUID box

- **Advanced Parallel Processing**:
  - Adaptive worker pool with resource monitoring
  - Automatic scaling based on system load
  - Progress tracking with ETA estimation
  - Memory-aware resource allocation

- **Memory-Efficient Processing**:
  - Streaming image processor for files of any size
  - Automatic chunking for memory optimization
  - Adaptive memory management
  - Support for very large files (>50MP)

- **Multi-page Document Support**:
  - Automatic detection and handling of multi-page TIFF files
  - Individual page extraction and processing
  - Options for skipping, overwriting, or maintaining existing files
  - Detailed reports for each page in multi-page documents

- **Color Profile Management**:
  - Automatic normalization of color profiles
  - Support for unusual color spaces (CMYK, LAB, etc.)
  - ICC profile preservation and conversion

- **Quality Analysis**:
  - PSNR (Peak Signal-to-Noise Ratio) calculation
  - SSIM (Structural Similarity Index) analysis
  - MSE (Mean Square Error) measurement

- **Configuration Management**:
  - Hierarchical configuration system
  - YAML and JSON configuration files
  - Environment variable override support
  - Schema validation with type checking

- **External Tool Integration**:
  - Automatic detection of Kakadu, ExifTool, and jpylyzer
  - Capability-based tool selection
  - Graceful fallbacks when tools aren't available
  - Version and compatibility checking

## Installation

### System Dependencies

Required external tools:
- **ExifTool** (required for metadata functionality):
  - On macOS: `brew install exiftool`
  - On Ubuntu/Debian: `sudo apt install libimage-exiftool-perl`
  - On Windows: Download from [ExifTool's website](https://exiftool.org)

- **JPylyzer** (required for proper JP2 validation):
  - `pip install jpylyzer`

If using the `--use-kakadu` option, Kakadu Software must be separately acquired and installed.

### Conda Environment (Recommended)

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge
cd jp2forge

# Create and activate conda environment
conda create -n jp2forge python=3.9
conda activate jp2forge

# Install dependencies
conda install -c conda-forge pillow numpy psutil exiftool lxml pyyaml
pip install jpylyzer
```

### Standard Installation

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge
cd jp2forge

# Install Python dependencies
pip install -r requirements.txt
pip install jpylyzer

# Don't forget to install system dependencies (ExifTool) as mentioned above
```

## Basic Usage

### Command-line Interface

Convert a single file:

```bash
python -m cli.workflow input.tif output_dir/
```

Process a directory:

```bash
python -m cli.workflow input_dir/ output_dir/ --recursive
```

Use parallel processing:

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

Enable detailed logging to a file:

```bash
python -m cli.workflow input_dir/ output_dir/ --verbose --log-file conversion.log
```

### Document Types

Select the document type based on your content:

```bash
python -m cli.workflow input_dir/ output_dir/ --document-type photograph
```

Available document types:
- `photograph`: Standard photographic images (default)
- `heritage_document`: Historical documents with high-quality settings
- `color`: General color images
- `grayscale`: Grayscale images

### Compression Modes

Select how compression is applied:

```bash
python -m cli.workflow input_dir/ output_dir/ --compression-mode supervised
```

Available compression modes:
- `supervised`: Quality-controlled compression (default)
- `lossless`: No data loss
- `lossy`: Higher compression with data loss
- `bnf_compliant`: BnF standards with fixed ratios

## BnF Compliance

Process files according to BnF standards:

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

> **Note**: JP2Forge supports BnF-compliant processing without requiring Kakadu, implementing all essential BnF parameters through our built-in Pillow integration. While Kakadu would provide more complete support for all BnF robustness markers (SOP, EPH, PLT), the default implementation adheres to core BnF standards using Pillow's parameters.

### BnF Compliance Capabilities

JP2Forge implements the following BnF specifications:

> **Note on Compression Ratio Notation**: BnF documentation uses 1:N notation while JP2Forge uses N:1 format. See [Notation Conventions](docs/NOTATION.md) for a detailed explanation.

#### Core Requirements (Fully Supported)
- **Compression Parameters**: Proper 9-7 floating wavelet transform (ICT)
- **BnF-specific Compression Ratios**: 4:1 (photograph/heritage), 6:1 (color), 16:1 (grayscale)
- **Tolerance Setting**: Configurable, default 5% as per BnF specs
- **Resolution Levels**: 10 levels as required
- **Progression Order**: RPCL as specified by BnF
- **Code Block Size**: 64x64 as specified
- **Tile Size**: 1024x1024 as specified

#### Metadata Handling (Fully Supported)
- **XMP Metadata Structure**: Fully compliant with BnF specifications
- **UUID Box**: Correctly implemented with BnF UUID format
- **Required Fields**: All required BnF metadata fields supported

#### Advanced Features (Partially Supported)
- **Robustness Markers**: Partial support for SOP, EPH, PLT markers (fully supported when using Kakadu)
- **Precinct Sizes**: Basic support for precinct size parameters

#### Validation
- **Compliance Checking**: Integration with jpylyzer for validation
- **Automated Verification**: BnF-specific validation checks

> **Ongoing Development**: We continue to enhance our BnF compliance capabilities and are working on testing and additional improvements to better adhere to all BnF specifications.

### BnF Document Types and Ratios

- `photograph` and `heritage_document`: 4:1 ratio
- `color`: 6:1 ratio
- `grayscale`: 16:1 ratio

### BnF Metadata

Provide BnF-compliant metadata:

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --metadata bnf_metadata.json
```

Example metadata.json:
```json
{
  "dcterms:isPartOf": "NUM_123456",
  "dcterms:provenance": "University Library",
  "dc:relation": "ark:/12148/cb123456789",
  "dc:source": "FOL-Z-123",
  "tiff:Model": "Phase One P45+",
  "tiff:Make": "Phase One",
  "aux:SerialNumber": "1234567890",
  "xmp:CreatorTool": "University Workflow",
  "tiff:Artist": "University Operator"
}
```

### Using Kakadu (Conceptual Implementation)

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --use-kakadu --kakadu-path=/path/to/kdu_compress
```

#### Important Note on Kakadu

Kakadu is a commercial software that requires a separate license for usage:

- **CONCEPTUAL IMPLEMENTATION**: The Kakadu integration is currently in conceptual status and has not been tested with actual Kakadu software
- Kakadu is **not included** with JP2Forge and must be acquired separately from [Kakadu Software](http://kakadusoftware.com/)
- A valid license is required to use Kakadu in production or commercial environments
- Using Kakadu with JP2Forge is entirely optional - the project works with Pillow for BnF-compliant processing
- The Kakadu integration code is provided as a reference implementation for how strict BnF compliance might be achieved in the future

## Mode Switching

### Normal Mode (Default)

```bash
python -m cli.workflow input_dir/ output_dir/
```

Options for normal mode:
```bash
python -m cli.workflow input_dir/ output_dir/ --compression-mode supervised --quality 40.0
```

### BnF Mode

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

Advanced BnF options:
```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --compression-ratio-tolerance 0.03
```

## Result Interpretation

### Processing Statuses

- **SUCCESS**: Successfully processed with all quality metrics above thresholds
- **WARNING**: Processed but quality metrics below thresholds
- **FAILURE**: Processing failed, no output file generated
- **SKIPPED**: File ignored (invalid image or corrupted)

### Summary Report

A summary report is generated that shows the overall results of batch processing and includes file size information for each file:

```
## Detailed Results
----------------
File: input_dir/example_photo_001.tif
Status: SUCCESS
Output: output_dir/example_photo_001.jp2
Original Size: 24.12 MB
Converted Size: 5.31 MB
Compression Ratio: 4.54:1

File: input_dir/example_photo_002.tif
Status: SUCCESS
Output: output_dir/example_photo_002.jp2
Original Size: 23.88 MB
Converted Size: 5.24 MB
Compression Ratio: 4.56:1

File: input_dir/example_photo_003.tif
Status: SUCCESS
Output: output_dir/example_photo_003.jp2
Original Size: 23.71 MB
Converted Size: 5.56 MB
Compression Ratio: 4.27:1
```

### Quality Metrics (Normal Mode)

- **PSNR**: Peak Signal-to-Noise Ratio (higher is better)
  - > 40 dB: Excellent quality
  - 30-40 dB: Good quality
  - < 30 dB: Medium to low quality

- **SSIM**: Structural Similarity Index (higher is better)
  - > 0.95: Excellent structural preservation
  - 0.90-0.95: Good structural preservation
  - < 0.90: More significant structural changes

- **MSE**: Mean Square Error (lower is better)

### Validation Reports

JP2Forge validates generated JPEG2000 files using JPylyzer, a specialized tool for validating JP2 files. The validation results are stored in `reports/info_jpylyzer.json` and include:

- Compliance with JP2 format specifications
- File structure validation
- Codestream properties validation
- Detailed box structure information
- Technical metadata extraction

**Important**: Installing JPylyzer (`pip install jpylyzer`) is strongly recommended for complete validation reports. Without JPylyzer, validation will be limited to basic file signature checks, and the "properties" fields in validation reports will be empty.

Example of JPylyzer validation properties:
```json
{
  "toolInfo": {
    "toolName": "jpylyzer",
    "toolVersion": "2.2.1"
  },
  "fileInfo": {
    "fileName": "example.jp2",
    "filePath": "/path/to/example.jp2",
    "fileSizeInBytes": "1993629"
  },
  "isValid": true,
  "properties": {
    "fileTypeBox": {
      "br": "jp2 ",
      "minV": "0",
      "cL": "jp2 "
    },
    "jp2HeaderBox": {
      "imageHeaderBox": {
        "height": "4311",
        "width": "3358",
        "nC": "3",
        "bPCSign": "unsigned",
        "bPCDepth": "8"
      },
      "colourSpecificationBox": {
        "meth": "Enumerated",
        "enumCS": "sRGB"
      }
    },
    "compressionRatio": "2.1"
  },
  "warnings": [],
  "validationTool": "jpylyzer",
  "validationToolVersion": "2.2.1"
}
```

### File Size Information

File size information is included in both individual file reports and the summary report:

- **Original Size**: Size of the input file (both in bytes and human-readable format)
- **Converted Size**: Size of the output JPEG2000 file (both in bytes and human-readable format)
- **Compression Ratio**: Ratio of original size to converted size (e.g., "4.50:1")

Example report with file size information:
```json
{
    "original_file": "example_photo_003.tif",
    "converted_file": "example_photo_003.jp2",
    "file_sizes": {
        "original_size": 24860832,
        "original_size_human": "23.71 MB",
        "converted_size": 5826410,
        "converted_size_human": "5.56 MB",
        "compression_ratio": "4.27:1"
    },
    "metrics": {
        "psnr": "44.52 dB",
        "ssim": "0.9998",
        "mse": "2.29"
    },
    "quality_passed": "yes",
    "thresholds": {
        "psnr": 40.0,
        "ssim": 0.95,
        "mse": 50.0
    },
    "recommendations": [
        "No quality issues detected. All metrics within acceptable thresholds."
    ]
}
```

This information helps you evaluate the effectiveness of different compression settings.

### Compression Ratio (BnF Mode)

BnF mode focuses on maintaining specific compression ratios within tolerance (default: 5%).

## Advanced Configuration

### Configuration Files

Save current configuration:
```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --save-config my_config.yaml
```

Use saved configuration:
```bash
python -m cli.workflow input_dir/ output_dir/ --config my_config.yaml
```

### Environment Variables

All configuration options can be set via environment variables:
```bash
export JP2FORGE_PROCESSING_MAX_WORKERS=4
export JP2FORGE_BNF_COMPLIANT=true
export JP2FORGE_JPEG2000_COMPRESSION_MODE=supervised
```

### Advanced Memory Management

```bash
# Process large images with streaming processor
python -m cli.workflow large_images/ output_dir/ --memory-limit 2048

# Force chunking for all images
python -m cli.workflow input_dir/ output_dir/ --force-chunking

# Set minimum chunk height for processing
python -m cli.workflow input_dir/ output_dir/ --min-chunk-height 32
```

### Parallel Processing Options

```bash
# Use adaptive worker pool with resource monitoring
python -m cli.workflow input_dir/ output_dir/ --parallel --adaptive-workers

# Set minimum and maximum worker count
python -m cli.workflow input_dir/ output_dir/ --parallel --min-workers 2 --max-workers 8

# Set resource thresholds for scaling
python -m cli.workflow input_dir/ output_dir/ --parallel --memory-threshold 0.8 --cpu-threshold 0.9
```

### Custom Color Management

```bash
# Preserve color profiles
python -m cli.workflow input_dir/ output_dir/ --preserve-icc-profiles

# Specify default color profiles
python -m cli.workflow input_dir/ output_dir/ --default-rgb-profile=/path/to/srgb.icc
```

## API Usage

### Standard Workflow

```python
from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

# Create configuration
config = WorkflowConfig(
    output_dir="output_dir/",
    report_dir="reports/",
    document_type=DocumentType.PHOTOGRAPH,
    compression_mode=CompressionMode.SUPERVISED,
    quality_threshold=40.0
)

# Create workflow
workflow = StandardWorkflow(config)

# Process a file
result = workflow.process_file("input.tif")
```

### Advanced Parallel Workflow

```python
from core.types import WorkflowConfig, ProcessingMode
from workflow.parallel import ParallelWorkflow
from utils.parallel.adaptive_pool import AdaptiveWorkerPool
from utils.parallel.progress_tracker import ProgressTracker

# Create advanced configuration
config = WorkflowConfig(
    output_dir="output_dir/",
    processing_mode=ProcessingMode.PARALLEL,
    max_workers=8,
    min_workers=2,
    memory_limit_mb=4096
)

# Create parallel workflow
workflow = ParallelWorkflow(config)

# Set up progress callback
def progress_callback(progress_data):
    print(f"Completed: {progress_data['percent_complete']:.1f}%, ETA: {progress_data['eta_time']}")

# Process a directory with progress tracking
results = workflow.process_directory(
    "input_dir/", 
    recursive=True,
    progress_callback=progress_callback
)
```

### Memory-Efficient Image Processing

```python
from utils.imaging.streaming_processor import StreamingImageProcessor

# Create streaming processor
processor = StreamingImageProcessor(
    memory_limit_mb=2048,
    min_chunk_height=16
)

# Process a large image
def enhance_image(img):
    # Image processing function
    return img.filter(ImageFilter.SHARPEN)

processor.process_in_chunks(
    "large_image.tif",
    "output.jp2",
    enhance_image,
    save_kwargs={'quality': 90}
)
```

### Working with Configuration

```python
from utils.config.config_manager import ConfigManager

# Create config manager
config_manager = ConfigManager()

# Load configuration from various sources
config_manager.load_from_file('config.yaml')
config_manager.load_from_env(prefix='JP2FORGE_')

# Get configuration values
output_dir = config_manager.get('output.directory', 'default_dir/')
max_workers = config_manager.get('processing.max_workers', 4)

# Validate configuration
is_valid, issues = config_manager.validate()
if not is_valid:
    for issue in issues:
        print(f"Configuration issue: {issue}")
```

## Troubleshooting

### Common Issues

#### Memory Issues with Large Images

If you encounter memory errors with large images:
- Use the streaming processor: `--memory-limit 2048`
- Adjust chunk size: `--min-chunk-height 32`
- Enable memory mapping: `--use-memory-mapping`

#### Slow Processing

If processing is slow:
- Use adaptive parallel processing: `--parallel --adaptive-workers`
- Adjust worker count: `--max-workers 8`
- Check for other resource-intensive processes running on your system

#### Metadata Issues

If metadata operations fail:
- Check if ExifTool is installed and accessible
- Use the tool manager to diagnose: `python -m utils.tools.tool_manager check`
- Try specifying ExifTool path explicitly: `--exiftool-path=/path/to/exiftool`

#### Configuration Problems

If configuration isn't being applied:
- Check for configuration file syntax errors
- Verify environment variable format (should be `JP2FORGE_SECTION_KEY=value`)
- Use `--debug` mode to see configuration loading details

## Intellectual Property

JP2Forge is designed with careful consideration for intellectual property rights:

- **Independent Implementation**: JP2Forge is an original implementation that doesn't reuse code from other JPEG2000 libraries like OpenJPEG
- **BnF Specifications**: Implementation follows published BnF technical specifications while acknowledging BnF's intellectual property
- **Third-Party Software**: 
  - Uses Pillow (permissive license) for basic operations
  - Optional Kakadu integration requires separate licensing and installation

For detailed information about intellectual property considerations, see the [IP Considerations Document](docs/IP_CONSIDERATIONS.md).

## Project Architecture

The project follows a modular architecture with well-defined components:

- **CLI Interface**: Entry point for command line operations
- **Workflow Components**: Manages processing pipeline (standard and parallel)
- **Core Components**: Handles compression, analysis, and metadata
- **Utility Modules**: Provides support for image processing, validation, etc.

For a detailed visual representation of the architecture and workflow, see the [JP2Forge Workflow Diagram](jp2forge-workflow.md).

## Project Origin and Implementation

JP2Forge is created by [xy-liao](https://github.com/xy-liao) and implements the JPEG2000 standard with BnF (Bibliothèque nationale de France) compliance. The implementation follows the technical specifications described in BnF reference documents.

### Implementation Note

JP2Forge is an independent implementation of the JPEG2000 standard with BnF compliance. It is not based on or derived from OpenJPEG's implementation. Instead, it relies on either Pillow or Kakadu (if available) for actual JPEG2000 encoding/decoding operations.

## Technical Specifications (BnF Standards)

### BnF JPEG2000 Parameters

- **Compression**: Irreversible (9-7 floating transform, ICT)
- **Compression Ratios**:
  - Specialized documents: 4:1
  - Exceptional documents: 4:1
  - Standard printed documents: 6:1
  - Grayscale transparent documents: 16:1
- **Tolerance**: 5% (configurable)
- **Fallback**: Lossless compression (5-3 integer transform, RCT) for files outside tolerance
- **Resolution Levels**: 10
- **Quality Levels**: 10
- **Progression Order**: RPCL (Resolution-Position-Component-Layer)
- **Robustness Markers**: SOP, EPH, PLT
- **Code Block Size**: 64x64
- **Tile Size**: 1024x1024
- **Precinct Size**: {256,256},{256,256},{128,128}

### BnF Metadata Structure

Required XMP metadata in UUID box (BE7ACFCB97A942E89C71999491E3AFAC):
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

## Project Origin and Acknowledgments

JP2Forge was created by [xy-liao](https://github.com/xy-liao) and was inspired by the BnF (Bibliothèque nationale de France) image format specifications. The implementation follows the technical requirements described in their reference documents.

### Implementation Note

JP2Forge is an independent implementation of the JPEG2000 standard with BnF compliance. It is not based on or derived from OpenJPEG's implementation. Instead, it relies on either Pillow or Kakadu (if available) for actual JPEG2000 encoding/decoding operations.

## JPEG2000 Library Comparison

There are several JPEG2000 implementations available. Here's how JP2Forge relates to them:

| Library | License | Relationship to JP2Forge |
|---------|---------|---------------------------|
| **Pillow** | HPND/PIL License (permissive) | Primary library used by JP2Forge for non-BnF compliant operations. |
| **Kakadu** | Commercial | Optional integration for BnF-compliant encoding. Users must acquire separately. |
| **OpenJPEG** | BSD 2-Clause | Not used by JP2Forge. Independent, open-source JPEG2000 codec. |
| **JasPer** | JasPer License (MIT-style) | Not used by JP2Forge. |
| **Grok/OpenJPH** | BSD 2-Clause | Not used by JP2Forge. |

JP2Forge is not derived from any of these implementations but rather uses Pillow's JPEG2000 support for basic operations and optionally interfaces with Kakadu for BnF-compliant processing when available.

## References

1. BnF Referential (2015): "Référentiel de format de fichier image v2" - [PDF](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)
2. BnF Documentation (2021): "Formats de données pour la préservation à long terme" - [PDF](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)
3. JPEG2000 Standard: ISO/IEC 15444
