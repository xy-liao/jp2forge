# JP2Forge 0.9.6 Release Notes

*Released: May 4, 2025*

JP2Forge 0.9.6 brings important fixes to report generation across all processing modes, adds new testing capabilities to ensure consistent performance, and fixes documentation issues on PyPI.

## What's New

- **Fixed PyPI README display issues** to ensure proper documentation on the package page
- **Fixed report generation issues** in single file processing mode
- **Added comprehensive test script** to validate JP2 conversion in different processing scenarios
- **Automated validation** of outputs and report generation across all processing modes
- **Improved parameter handling** for multi-page TIFF processing
- **Fixed memory-efficient processing trigger logic** to properly respect both memory_limit_mb and chunk_size parameters
- **Enhanced chunking mechanism** to ensure proper resource utilization during large TIFF processing

## Detailed Changes

### Bug Fixes

- Fixed PyPI README display issues to properly represent features and usage
- Fixed issues where report generation might fail in single file processing mode
- Fixed inconsistencies in report generation between single file and directory processing modes
- Fixed memory-efficient processing trigger logic to better handle both memory_limit_mb and chunk_size parameters
- Enhanced chunking mechanism to ensure proper resource utilization during large TIFF processing
- Improved parameter handling for multi-page TIFF processing

### New Features

- Added test_jp2forge.sh script to validate single file and batch processing functionality
- Added automated validation of outputs and report generation across all processing modes
- Added comprehensive testing for various JP2Forge use cases

## Test Suite

The new test script (test_jp2forge.sh) validates JP2Forge in three different scenarios:

1. **Single file processing mode** - Tests direct conversion of a single image
2. **Single file from directory** - Tests processing a single file specified by path in a directory
3. **Multiple file batch processing** - Tests processing all files in a directory

For each test scenario, the script validates:
- Successful JP2 file generation in the output directory
- Proper JPylyzer validation report creation
- Summary report generation with appropriate statistics
- Complete cleanup between tests

## Upgrading

To upgrade to JP2Forge 0.9.6:

```bash
# If installed from git repository
git fetch
git checkout v0.9.6
pip install -r requirements.txt

# If installed via pip
pip install --upgrade jp2forge
```

## Contributors

Thanks to all who contributed to this release!