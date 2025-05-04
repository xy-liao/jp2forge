# Changelog

All notable changes to JP2Forge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.6] - 2025-05-04

### Fixed
- Fixed PyPI README display issues
- Improved parameter handling for multi-page TIFF processing
- Fixed memory-efficient processing trigger logic to properly respect both memory_limit_mb and chunk_size parameters
- Enhanced chunking mechanism to ensure proper resource utilization during large TIFF processing
- Fixed report generation issues in single file processing mode

### Added
- New test_jp2forge.sh script to validate single file and batch processing functionality
- Automated validation of outputs and report generation across all processing modes

## [0.9.5] - 2025-05-04

### Fixed
- Improved parameter handling for multi-page TIFF processing
- Fixed memory-efficient processing trigger logic to properly respect both memory_limit_mb and chunk_size parameters
- Enhanced chunking mechanism to ensure proper resource utilization during large TIFF processing
- Fixed report generation issues in single file processing mode
- Added comprehensive test script for validating JP2 conversion in different scenarios

### Added
- New test_jp2forge.sh script to validate single file and batch processing functionality
- Automated validation of outputs and report generation across all processing modes