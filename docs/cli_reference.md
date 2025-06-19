# JP2Forge CLI Reference

This document provides a comprehensive reference for all available command-line arguments in JP2Forge.

## Basic Usage

```bash
python -m cli.workflow <input_path> <output_directory> [options]
```

Where:
- `<input_path>`: Path to an image file or directory
- `<output_directory>`: Directory where converted images will be saved

## All Available Options

### Core Options

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version information and exit | |
| `--document-type {photograph,heritage_document,color,grayscale}` | Type of document being processed | `photograph` |
| `--compression-mode {lossless,lossy,supervised,bnf_compliant}` | Compression mode to use | `supervised` |
| `--bnf-compliant` | Use BnF compliant settings | `False` |
| `--recursive`, `-r` | Process subdirectories recursively | `False` |
| `--config` | Path to configuration file | |
| `--save-config` | Save configuration to JSON file | |
| `--metadata` | Path to JSON file containing metadata | |
| `--overwrite` | Overwrite existing files | `False` |
| `--skip-existing` | Skip existing files | `False` |

### Compression Options

| Option | Description | Default |
|--------|-------------|---------|
| `--quality` | Quality threshold for compression (PSNR) | `40.0` |
| `--resolutions` | Number of resolution levels | `10` |
| `--progression` | Progression order for JPEG2000 | `RPCL` |
| `--compression-ratio` | Target compression ratio (e.g., 20 for 20:1 compression) | |
| `--target-size` | Target size in bytes for compressed images | |
| `--compression-ratio-tolerance` | Tolerance for compression ratio | `0.05` (5%) |
| `--no-lossless-fallback` | Disable fallback to lossless compression | `False` |
| `--no-compression` | Skip compression step (for debugging) | `False` |
| `--no-upscale` | Don't upscale images to minimum dimensions | `False` |

### BnF Compliance Options

| Option | Description | Default |
|--------|-------------|---------|
| `--include-bnf-markers` | Include BnF robustness markers (SOP, EPH, PLT) | `True` |

### Parallel Processing Options

| Option | Description | Default |
|--------|-------------|---------|
| `--parallel` | Use parallel processing | `False` |
| `--max-workers` | Maximum number of worker processes | CPU count - 1 |
| `--threads` | Alias for --max-workers | |
| `--adaptive-workers` | Enable adaptive worker pool scaling based on system resources | `False` |
| `--min-workers` | Minimum number of worker processes for adaptive scaling | `1` |
| `--memory-threshold` | Memory usage threshold (0-1) for adaptive scaling | `0.8` |
| `--cpu-threshold` | CPU usage threshold (0-1) for adaptive scaling | `0.9` |
| `--collector-batch-size` | Number of files to process in a batch | `10` |
| `--collector-threads` | Number of threads to use for collection | `1` |
| `--converter-threads` | Number of threads to use for conversion | Same as max-workers |

### Memory Management Options

| Option | Description | Default |
|--------|-------------|---------|
| `--memory-limit` | Memory limit in MB for adaptive processing | `4096` |
| `--chunk-size` | Number of pixels to process at once for large images | `1000000` |
| `--keep-temp` | Keep temporary files | `False` |

### Logging Options

| Option | Description | Default |
|--------|-------------|---------|
| `--verbose`, `-v` | Enable verbose logging | `False` |
| `--log-file` | Path to log file | |
| `--logfile` | Alias for --log-file | |
| `--loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}` | Logging level | `INFO` |
| `--debug` | Enable debug mode (shorthand for --loglevel=DEBUG) | |
| `--report-dir` | Directory for analysis reports | `reports` |
| `--full-report` | Generate detailed reports with quality metrics, processing times, and enhanced validation | `False` |
| `--strict` | Enable strict mode for error handling | `False` |

## Environment Variables

All command-line options can be set via environment variables with the `JP2FORGE_` prefix and uppercase option name. For example:

```bash
export JP2FORGE_COMPRESSION_MODE=lossy
export JP2FORGE_QUALITY=50
export JP2FORGE_PARALLEL=true
```

## Configuration Files

You can save and load configurations using JSON files:

```bash
# Save current configuration
python -m cli.workflow input_dir/ output_dir/ --compression-mode lossy --save-config my_config.json

# Use a saved configuration
python -m cli.workflow input_dir/ output_dir/ --config my_config.json
```

## Examples

### Basic Usage

```bash
# Convert a single file
python -m cli.workflow input.tif output_dir/

# Process a directory with parallel processing
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4

# BnF-compliant conversion
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### Advanced Usage

```bash
# Memory-efficient processing of large images
python -m cli.workflow large_image.tif output_dir/ --memory-limit 2048 --chunk-size 5000000

# Production-grade parallel processing
python -m cli.workflow input_dir/ output_dir/ --parallel --adaptive-workers --min-workers 2 --memory-threshold 0.7 --cpu-threshold 0.8

# BnF compliant with metadata
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant --metadata metadata.json

# Full report with detailed quality metrics
python -m cli.workflow input_dir/ output_dir/ --full-report --parallel --max-workers 4
```
