# Benchmark Output Directory

This directory contains JPEG2000 files generated during benchmark tests.

## Contents

This directory will contain:
- Converted JP2 files from benchmark test runs
- Files used for comparing different compression settings

## Example Usage

Benchmark files are generated when running benchmark tests:

```bash
python -m utils.benchmark --test-suite standard
```

## File Organization

Files in this directory:
- Benchmark output files follow a naming convention with parameters encoded in filenames
- Files may be organized in subdirectories based on the benchmark type

## Usage Notes

Output files are not included in the repository but will be generated when you run benchmarks.
