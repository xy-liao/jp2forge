# Changelog

All notable changes to JP2Forge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Improved parameter handling for multi-page TIFF processing
- Fixed memory-efficient processing trigger logic to properly respect both memory_limit_mb and chunk_size parameters
- Enhanced chunking mechanism to ensure proper resource utilization during large TIFF processing

## [0.9.2] - 2025-04-28

### Changed
- Updated package metadata in PyPI distribution for privacy improvements
- Removed email information from public package metadata

## [0.9.1] - 2025-04-24

### Changed
- Renamed directory paths from "images/" to "input_dir/" and "output_dir/" to "output_dir/" for better alignment with documentation examples
- Updated cleanup script to handle both old and new directory structures for backward compatibility

## [0.9.0] - 2025-04-19

### Fixed
- Improved color profile handling for compatibility with modern Pillow versions
- Added robust fallback methods for color profile conversion
- Fixed benchmark directory structure for cleaner repository organization

### Changed
- Updated from beta to full release version
- Enhanced cleanup utility to properly manage benchmark directories
- Improved repository preparation for publication

## [0.9.0-beta] - 2025-04-15

### Added
- File size reporting to individual JSON reports and summary reports
- Original file size, converted file size, and compression ratio information
- Human-readable file size formatting
- Comprehensive intellectual property documentation and clarifications
- IP_CONSIDERATIONS.md document explaining the project's relationship with other implementations
- JPEG2000 library comparison section to README.md
- Comprehensive documentation suite with architecture document, developer guide, and user guide
- Detailed performance benchmarking framework and optimization guidance
- Code quality checklist for ensuring consistent code quality
- Implementation schedule with prioritized roadmap for future development
- Advanced parallel processing with adaptive worker pool and memory monitoring
- Progress tracking with ETA estimation and status reporting
- Memory-efficient streaming image processor for extremely large images
- XML processing with proper namespace handling using lxml
- Hierarchical configuration system with schema validation
- External tool management for Kakadu and ExifTool
- Memory usage estimation for different image types and operations
- BnF-specific metadata handler class
- XMP utilities for metadata creation and validation
- Support for large image processing via chunking
- Color profile normalization for unusual color spaces

### Changed
- Standardized docstrings across the project to consistently use "JP2Forge" name
- Updated default software name in metadata from "JPEG2000 Workflow" to "JP2Forge"
- Enhanced module-level documentation for better consistency
- Improved project metadata in setup.py
- Enhanced docstrings with usage examples and detailed parameter descriptions
- Added system architecture diagrams with component interactions
- Improved parallel processing with dynamic worker scaling
- Replaced string-based XML handling with lxml for proper XML processing
- Extracted hardcoded values to configuration parameters
- Added capability-based tool selection with fallbacks
- Improved error handling for file operations and subprocess calls

### Fixed
- Inconsistencies between code documentation and implementation
- Documentation gaps for extension points and customization
- Memory leaks during large image processing
- Thread safety issues in parallel processing
- Namespace handling in XMP metadata
- Error propagation in subprocess tool execution
- Temporary file cleanup in error scenarios
- Improved error handling for missing output directories

## [0.1.0] - 2025-01-30

### Added
- Initial release of JP2Forge
- Support for converting images to JPEG2000 format
- BnF-compliant conversion mode
- Parallel processing support
- Quality analysis with pixel loss assessment
- Metadata handling