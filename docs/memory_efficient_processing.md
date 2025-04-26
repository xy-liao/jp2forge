# Memory-Efficient Processing in JP2Forge

This document provides detailed technical information about JP2Forge's memory-efficient processing capabilities, particularly for handling multi-page TIFF files and large images.

## Table of Contents

1. [Introduction](#1-introduction)
2. [Memory Usage Challenges](#2-memory-usage-challenges)
3. [Memory-Efficient Processing Architecture](#3-memory-efficient-processing-architecture)
4. [Configuration Parameters](#4-configuration-parameters)
5. [Implementation Details](#5-implementation-details)
6. [Best Practices](#6-best-practices)
7. [Performance Considerations](#7-performance-considerations)
8. [Advanced Configuration](#8-advanced-configuration)
9. [Troubleshooting](#9-troubleshooting)

## 1. Introduction

JP2Forge includes specialized memory-efficient processing capabilities designed to handle very large images and multi-page documents without excessive memory consumption. This is achieved through a combination of chunked processing, streaming algorithms, and parameter-controlled resource utilization.

## 2. Memory Usage Challenges

### 2.1 Large Image Processing

Processing large images presents several memory challenges:

- TIFF decoding typically requires the entire decompressed image to be loaded into memory
- JPEG2000 compression algorithms require additional memory for wavelet transforms
- Quality analysis requires both source and output images to be available simultaneously
- Color profile transformations may require additional memory

### 2.2 Multi-page TIFF Processing

Multi-page TIFFs add further complexity:

- Each page may be a large image itself
- Loading multiple pages simultaneously can quickly exhaust available memory
- Sequential page processing requires careful resource management
- Temporary files need to be managed efficiently

## 3. Memory-Efficient Processing Architecture

JP2Forge's memory-efficient processing is built on these core strategies:

### 3.1 Chunked Processing

- Images are processed in horizontal strips or chunks
- Each chunk is processed independently and then combined
- Memory usage is proportional to chunk size rather than total image size
- Chunks are processed sequentially to minimize memory footprint

### 3.2 Streaming Processing

- Input data is read progressively as needed
- Output data is written incrementally
- Intermediate results are discarded when no longer needed
- Processing state is maintained for incremental processing

### 3.3 Memory Monitoring

- Memory usage is tracked during processing
- If usage approaches limits, processing adapts dynamically
- Resources are released proactively when no longer needed
- Garbage collection is triggered at appropriate points

## 4. Configuration Parameters

Two primary parameters control memory-efficient processing:

### 4.1 Memory Limit Parameter (`memory_limit_mb`)

The `memory_limit_mb` parameter sets a target memory limit in megabytes:

- **Default value**: 4096 (4 GB)
- **Effect**: When estimated memory usage exceeds this limit, memory-efficient processing is activated
- **Trigger**: JP2Forge calculates approximate memory requirements based on image dimensions and bit depth
- **Recommendation**: Set to 50-75% of available system RAM

### 4.2 Chunk Size Parameter (`chunk_size`)

The `chunk_size` parameter controls how many pixels are processed at once:

- **Default value**: 1,000,000 pixels
- **Effect**: Controls the height of each horizontal strip processed
- **Calculation**: `chunk_height = chunk_size / image_width`
- **Trigger**: Values below 1,000,000 pixels will always trigger memory-efficient processing
- **Recommendation**: 250,000-500,000 for memory-constrained environments

### 4.3 Parameter Interaction

- Either parameter can independently trigger memory-efficient processing
- When both parameters are specified, the most conservative (lowest memory) approach is used
- Memory estimations account for both parameters to optimize resource usage

## 5. Implementation Details

### 5.1 Memory Usage Estimation

JP2Forge estimates memory requirements using this formula:

```
estimated_memory_mb = (width * height * channels * bytes_per_channel * 3) / (1024 * 1024)
```

The multiplier of 3 accounts for:
- Source image in memory
- Intermediate processing buffers
- Output data before writing

### 5.2 Chunk Height Calculation

Chunk height is calculated dynamically:

```python
chunk_height = min(
    image_height,
    max(
        32,  # Minimum chunk height
        chunk_size // image_width
    )
)
```

### 5.3 Processing Flow

The memory-efficient processing flow:

1. Image dimensions and properties are determined without loading the full image
2. Memory requirements are estimated and compared to the memory limit
3. If necessary, memory-efficient mode is activated
4. Image is processed in chunks of calculated height
5. Each chunk is processed through the full pipeline and then released
6. Results are combined into the final output

## 6. Best Practices

### 6.1 Determining Optimal Parameters

To determine optimal parameters for your environment:

1. Start with default parameters and monitor memory usage
2. If memory usage is too high, reduce `memory_limit_mb` to 50% of available RAM
3. For further reduction, set `chunk_size` to 500,000
4. For very memory-constrained environments, use both parameters together

### 6.2 Recommended Configurations

| System Memory | Recommended Settings |
|---------------|---------------------|
| 4 GB or less | `memory_limit_mb=1536, chunk_size=250000` |
| 8 GB | `memory_limit_mb=4096, chunk_size=500000` |
| 16 GB | `memory_limit_mb=8192` (default chunk_size) |
| 32 GB+ | Default parameters |

### 6.3 Multi-page TIFF Processing

For multi-page TIFFs:

- Each page is loaded independently
- Memory is released between pages
- Parameters apply to each page individually
- Default parameters work well for documents with moderate page sizes
- Adjust parameters for documents with very large pages

## 7. Performance Considerations

### 7.1 Memory vs. Performance Tradeoffs

Memory-efficient processing introduces some performance tradeoffs:

- Processing in chunks can be slower than whole-image processing
- Smaller chunks increase overhead but reduce memory usage
- Very small chunks may significantly impact performance
- I/O operations increase with smaller chunk sizes

### 7.2 Benchmarks

Performance impact of memory-efficient processing (relative to whole-image processing):

| Image Size | Chunk Size | Memory Usage | Processing Time Impact |
|------------|------------|--------------|------------------------|
| 100 MP | 1,000,000 | ~1.2 GB | +5-10% |
| 100 MP | 500,000 | ~650 MB | +10-15% |
| 100 MP | 250,000 | ~350 MB | +15-25% |
| 500 MP | 1,000,000 | ~5.5 GB | +3-8% |
| 500 MP | 500,000 | ~3 GB | +8-12% |
| 500 MP | 250,000 | ~1.5 GB | +12-20% |

### 7.3 Optimization Tips

To minimize performance impact:

- Use the largest chunk size that fits within your memory constraints
- Enable memory mapping with `--use-memory-mapping` for improved I/O performance
- For batch processing, adjust parallel worker count to balance CPU and memory usage
- Place temporary files on fast storage (SSD) when possible

## 8. Advanced Configuration

### 8.1 Combining with Parallel Processing

When combining memory-efficient processing with parallel execution:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --parallel \
  --memory-limit-mb 2048 \
  --chunk-size 500000 \
  --max-workers 4
```

JP2Forge will automatically adjust worker count based on memory requirements.

### 8.2 Environment-Specific Settings

For containerized environments with limited memory:

```bash
python -m cli.workflow input_dir/ output_dir/ \
  --memory-limit-mb 1024 \
  --chunk-size 250000 \
  --use-memory-mapping
```

### 8.3 Per-File Configuration

For workflows with varying file sizes, consider dynamic configuration:

```python
from core.types import WorkflowConfig
from workflow.standard import StandardWorkflow

def process_with_adaptive_memory(file_path):
    # Determine image size and set parameters accordingly
    from PIL import Image
    img = Image.open(file_path)
    width, height = img.size
    img.close()
    
    # Calculate total pixels
    total_pixels = width * height
    
    # Set parameters based on image size
    if total_pixels > 100_000_000:  # > 100 MP
        config = WorkflowConfig(
            memory_limit_mb=2048,
            chunk_size=250000
        )
    elif total_pixels > 50_000_000:  # > 50 MP
        config = WorkflowConfig(
            memory_limit_mb=4096,
            chunk_size=500000
        )
    else:
        config = WorkflowConfig()  # Default parameters
    
    workflow = StandardWorkflow(config)
    return workflow.process_file(file_path)
```

## 9. Troubleshooting

### 9.1 Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| Memory errors despite settings | Inaccurate memory estimation | Lower both parameters further |
| Extremely slow processing | Chunk size too small | Increase chunk size if memory allows |
| Corrupted output images | Chunk combination issues | Use default parameters or larger chunk size |
| Processing fails on specific pages | Page-specific complexity | Process problematic pages with smaller chunk size |

### 9.2 Diagnostic Tools

To diagnose memory usage issues:

```bash
python -m cli.workflow input.tif output_dir/ \
  --verbose \
  --log-file memory_log.txt \
  --profile-memory
```

### 9.3 Memory Issue Resolution

Steps to resolve persistent memory issues:

1. Enable verbose logging to identify problematic processing stages
2. Reduce chunk size incrementally until processing succeeds
3. If issues persist, try processing files individually rather than in batch
4. For multi-page TIFFs, consider extracting and processing pages separately
5. Use the memory profiling tool to identify specific memory usage patterns