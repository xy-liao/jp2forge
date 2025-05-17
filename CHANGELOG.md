# Changelog

All notable changes to JP2Forge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Upcoming] - Implementation Roadmap Created

- Added comprehensive [Implementation Roadmap](docs/implementation_roadmap.md) outlining planned improvements
- Identified BnF compliance gaps to be addressed in upcoming releases
- Scheduled improvements for architecture, testing, and documentation

## [Unreleased]

### Added
- Comprehensive [CLI Reference](docs/cli_reference.md) documentation covering all command-line arguments
- Updated user guide with expanded information on compression modes and document types
- Improved documentation consistency between implementation and documentation
- Enhanced user guide sections on BnF compression ratios for different document types

## [0.9.6] - 2025-05-05

### Fixed
- Fixed PyPI README display issues
- Improved parameter handling for multi-page TIFF processing
- Fixed memory-efficient processing trigger logic to properly respect both memory_limit_mb and chunk_size parameters
- Enhanced chunking mechanism to ensure proper resource utilization during large TIFF processing
- Fixed report generation issues in single file processing mode

### Added
- New test_jp2forge.sh script to validate single file and batch processing functionality
- Automated validation of outputs and report generation across all processing modes

## [0.9.5] - 2025-04-28

### Fixed
- Initial fix for memory-efficient processing trigger logic
- Preliminary improvements to chunking mechanism
- Basic report generation fixes for batch processing mode

### Added
- Draft version of test script for JP2 validation