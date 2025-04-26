# JP2Forge Performance Benchmarks and Optimization Guide

This document provides guidelines for performance testing, benchmarking, and optimization of the JP2Forge library. It serves as a reference for developers to ensure consistent performance across releases and identify optimization opportunities.

## Table of Contents

1. [Performance Testing Infrastructure](#1-performance-testing-infrastructure)
2. [Key Performance Metrics](#2-key-performance-metrics)
3. [Benchmark Datasets](#3-benchmark-datasets)
4. [Running Benchmarks](#4-running-benchmarks)
5. [Current Performance Baselines](#5-current-performance-baselines)
6. [Performance Bottlenecks](#6-performance-bottlenecks)
7. [Optimization Guidelines](#7-optimization-guidelines)
8. [Memory Optimization](#8-memory-optimization)
9. [CPU Optimization](#9-cpu-optimization)
10. [I/O Optimization](#10-io-optimization)

## 1. Performance Testing Infrastructure

JP2Forge uses a consistent testing environment for performance evaluation:

### 1.1 Benchmark Utility

The benchmarking utility is located in `/utils/benchmarks/`:

```bash
# Run standard benchmark suite
python -m utils.benchmarks.run_benchmark

# Run specific benchmark
python -m utils.benchmarks.run_benchmark --test compression
```

### 1.2 Standard Test Environment

All official benchmarks are run on standardized hardware:

* **CPU**: Intel Core i7-12700K (12 cores/20 threads)
* **RAM**: 32GB DDR5-4800
* **Storage**: NVMe SSD (>3000MB/s sequential read/write)
* **OS**: Ubuntu 22.04 LTS
* **Python**: 3.9.10

### 1.3 Reporting

Benchmark results include:

* Raw timing data
* Statistical analysis (mean, median, stddev)
* Comparison to baseline
* Memory usage tracking
* CPU utilization data
* Profiling hotspots

## 2. Key Performance Metrics

The following metrics are tracked for performance evaluation:

### 2.1 Timing Metrics

* **Single-file processing time**: Time to process a single image
* **Batch processing throughput**: Images processed per minute
* **Initialization time**: Time to initialize a workflow
* **Compression time**: Time spent in compression operations
* **Analysis time**: Time spent in quality analysis
* **Metadata time**: Time spent in metadata operations
* **Total workflow time**: End-to-end processing time

### 2.2 Resource Utilization Metrics

* **Peak memory usage**: Maximum memory consumed during processing
* **Average memory usage**: Average memory consumption
* **CPU utilization**: Average CPU usage percentage
* **Thread utilization**: Effectiveness of parallelization
* **I/O wait time**: Time spent waiting for I/O operations

### 2.3 Scalability Metrics

* **Worker scaling efficiency**: Performance improvement per additional worker
* **Memory scaling**: How memory usage scales with image size
* **Large batch scaling**: Performance with increasing batch sizes
* **Multi-core efficiency**: Parallelization effectiveness

## 3. Benchmark Datasets

Standard test datasets are used for consistent performance evaluation:

### 3.1 Standard Test Images

| Dataset | Description | Size | Count | Location |
|---------|-------------|------|-------|----------|
| small | Small images (<2MP) | ~20MB | 100 | /benchmark/data/small/ |
| medium | Medium images (2-10MP) | ~200MB | 50 | /benchmark/data/medium/ |
| large | Large images (10-50MP) | ~1GB | 20 | /benchmark/data/large/ |
| huge | Very large images (>50MP) | ~2GB | 5 | /benchmark/data/huge/ |
| mixed | Mixed sizes and types | ~1GB | 100 | /benchmark/data/mixed/ |

### 3.2 Specialized Test Sets

* **color_profiles**: Images with various color profiles
* **metadata_rich**: Images with extensive metadata
* **challenging**: Images known to be challenging for compression
* **bnf_samples**: Images matching BnF document categories

## 4. Running Benchmarks

### 4.1 Basic Benchmark

Run the basic benchmark suite:

```bash
python -m utils.benchmarks.run_benchmark
```

### 4.2 Specific Benchmarks

Run specific performance tests:

```bash
# Test compression performance
python -m utils.benchmarks.run_benchmark --test compression

# Test parallel processing with different worker counts
python -m utils.benchmarks.run_benchmark --test parallel --workers 1,2,4,8,16

# Test memory usage with large images
python -m utils.benchmarks.run_benchmark --test memory --dataset huge

# Test BnF compliance performance
python -m utils.benchmarks.run_benchmark --test bnf --document-type color
```

### 4.3 Profile-Guided Optimization

Generate profiling data:

```bash
python -m utils.benchmarks.run_profile --output profile_data.prof
```

Analyze profiling data:

```bash
python -m utils.benchmarks.analyze_profile profile_data.prof
```

## 5. Current Performance Baselines

These baselines represent current performance on the standard test environment:

### 5.1 Single-File Processing (Standard Workflow)

| Image Size | Compression Mode | Processing Time | Memory Usage |
|------------|------------------|----------------|--------------|
| Small (1MP) | lossless | 0.8s | 120MB |
| Small (1MP) | lossy | 0.7s | 115MB |
| Medium (5MP) | lossless | 2.5s | 350MB |
| Medium (5MP) | lossy | 2.1s | 320MB |
| Large (20MP) | lossless | 8.3s | 980MB |
| Large (20MP) | lossy | 7.1s | 920MB |
| Huge (80MP) | lossless | 29.6s | 3.2GB |
| Huge (80MP) | lossy | 26.2s | 3.0GB |

### 5.2 Batch Processing Performance (50 Medium Images)

| Worker Count | Total Time | Images/Minute | Memory Usage | CPU Usage |
|--------------|------------|---------------|--------------|-----------|
| 1 | 125.0s | 24.0 | 450MB | 23% |
| 2 | 65.8s | 45.6 | 780MB | 45% |
| 4 | 35.2s | 85.2 | 1.4GB | 87% |
| 8 | 33.5s | 89.6 | 2.5GB | 92% |
| 16 | 32.8s | 91.5 | 3.8GB | 94% |

### 5.3 BnF Compliance Mode

| Document Type | Ratio | Processing Time | Memory Usage |
|---------------|-------|----------------|--------------|
| photograph | 1:4 | 3.2s | 380MB |
| heritage_document | 1:4 | 3.5s | 390MB |
| color | 1:6 | 2.8s | 360MB |
| grayscale | 1:16 | 1.9s | 280MB |

## 6. Performance Bottlenecks

Analysis has identified these main performance bottlenecks:

### 6.1 Current Bottlenecks

1. **Image Decompression**: Initial loading and decompression of source images
2. **Wavelet Transform**: Computation of wavelet transforms during compression
3. **Memory Fragmentation**: In batch processing of multiple large images
4. **External Tool Execution**: When using Kakadu for BnF-compliant processing
5. **Quality Analysis**: SSIM calculation for large images

### 6.2 I/O Bottlenecks

* Large file reading during streaming processing
* Metadata extraction with ExifTool subprocess calls
* Temporary file creation during processing

### 6.3 CPU Bottlenecks

* Wavelet coefficient calculation
* Quality metric computation (especially SSIM)
* Color space conversions

### 6.4 Memory Bottlenecks

* Full image loading for non-chunked processing
* Multiple images in parallel processing
* Intermediate data structures during compression

## 7. Optimization Guidelines

Follow these guidelines when optimizing JP2Forge code:

### 7.1 General Principles

1. **Measure first**: Always establish a baseline before optimization
2. **Focus on hot spots**: Optimize functions identified in profiling
3. **Test thoroughly**: Ensure optimizations don't affect output quality
4. **Document tradeoffs**: Note any quality/performance tradeoffs
5. **Validate improvements**: Verify performance gain with benchmarks

### 7.2 Optimization Priority

Optimize in this order for maximum impact:

1. **Algorithms**: Improve algorithmic complexity first
2. **I/O operations**: Minimize disk access and improve buffering
3. **Memory usage**: Reduce peak memory requirements
4. **CPU efficiency**: Optimize computationally intensive sections
5. **Parallelization**: Improve parallel processing efficiency

### 7.3 Code-Level Optimization

* Use vectorized operations with NumPy where applicable
* Replace Python loops with optimized C/Cython functions for critical paths
* Consider JIT compilation with Numba for compute-intensive functions
* Use appropriate data structures for specific operations

## 8. Memory Optimization

### 8.1 Key Strategies

* **Streaming processing**: Process large images in chunks
* **Memory mapping**: Use memory-mapped file access for large files
* **Resource pooling**: Reuse allocated resources
* **Garbage collection**: Force collection after large operations
* **Buffer reuse**: Reuse buffers instead of creating new ones

### 8.2 Large Image Handling

For images > 50MP:

* Always use streaming processor
* Set appropriate chunk size:
  ```python
  # Optimal chunk size based on available memory
  chunk_height = min(32, max(16, (available_memory_mb * 0.8) // (image_width * 3 // 1024)))
  ```
* Monitor memory usage in real-time during processing

### 8.3 Parallel Processing Memory Management

* Limit concurrent workers based on available memory:
  ```python
  # Recommended formula
  max_workers = min(cpu_count, (available_memory_gb * 0.7) // memory_per_image_gb)
  ```
* Implement backpressure mechanisms in work queues
* Consider process-based parallelism for better memory isolation

## 9. CPU Optimization

### 9.1 Vectorization

* Use NumPy vectorized operations:
  ```python
  # Instead of:
  for i in range(height):
      for j in range(width):
          result[i, j] = source[i, j] * factor
  
  # Use:
  result = source * factor
  ```

### 9.2 Parallelization

* Optimize chunk size for parallel processing:
  ```python
  # Recommended chunk size formula
  optimal_chunk_size = max(16, min(image_height // (4 * worker_count), 64))
  ```
* Use thread pooling for I/O-bound operations
* Use process pooling for CPU-bound operations

### 9.3 NumPy and SciPy Optimization

* Use built-in functions rather than custom implementations
* Minimize array copies:
  ```python
  # Instead of:
  temp = array.copy()
  temp += 1
  
  # Use:
  array += 1
  ```
* Use views instead of copies when possible
* Consider using `numexpr` for complex expressions

## 10. I/O Optimization

### 10.1 File Access Patterns

* Use appropriate buffer sizes:
  ```python
  # For large files
  with open(file_path, 'rb', buffering=1024*1024) as f:
      data = f.read()
  ```
* Use memory mapping for large files:
  ```python
  with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
      data = mm[start:end]
  ```
* Batch small I/O operations

### 10.2 External Tool Optimization

* Minimize ExifTool subprocess calls by batching operations
* Cache tool results when processing multiple similar files
* Use pipe communication instead of temporary files when possible

### 10.3 Temporary Files

* Use memory-based temporary storage for small files
* Place temporary files on fast storage
* Clean up temporary files promptly
* Use unique names to avoid conflicts in parallel processing
