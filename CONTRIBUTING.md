# Contributing to JP2Forge

Thank you for your interest in contributing to JP2Forge! This project aims to provide a comprehensive solution for JPEG2000 conversion with BnF compliance, and community contributions are essential to make it better.

## Getting Started

Before you begin:

1. Ensure you have a [GitHub account](https://github.com/signup/free)
2. Familiarize yourself with the [project documentation](README.md)
3. Set up your development environment as described in the installation instructions

## Ways to Contribute

There are many ways to contribute to JP2Forge:

### Reporting Bugs

If you find a bug, please create an issue on our GitHub repository with:

- A clear, descriptive title
- A detailed description of the issue
- Steps to reproduce the problem
- Expected vs. actual behavior
- Environment details (OS, Python version, etc.)
- Any additional context or screenshots

### Suggesting Enhancements

We welcome suggestions for new features or improvements:

- Use a clear, descriptive title
- Provide a step-by-step description of the enhancement
- Explain why this enhancement would be useful
- Include any relevant examples or mock-ups

### Code Contributions

If you'd like to contribute code:

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Write your code, following our coding conventions
4. Add tests for your changes
5. Ensure all tests pass
6. Submit a pull request

## Development Process

### Setting Up Your Environment

```bash
# Clone your fork of the repository
git clone https://github.com/xy-liao/jp2forge.git

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Coding Standards

- Follow PEP 8 style guidelines
- Write docstrings for all functions, classes, and modules
- Include type hints where appropriate
- Keep functions focused and maintainable (under 50 lines when possible)
- Write clear, descriptive variable and function names

### Metadata Handling Guidelines

When contributing to metadata handling, consider these key principles:

1. **Robust Initialization**
   - Always provide fallback mechanisms for metadata handlers
   - Handle cases where ExifTool might not be available
   - Provide meaningful error messages and logging

2. **ExifTool Compatibility**
   - Ensure code works across different ExifTool versions
   - Handle variations in ExifTool output formats
   - Implement thorough error checking and recovery

3. **Validation**
   - Implement strict validation for metadata fields
   - Support both standard and BnF-specific metadata requirements
   - Normalize metadata to ensure consistency

Example of robust metadata handler design:
```python
def __init__(self, base_handler=None, debug=False):
    """
    Initialize metadata handler with fallback and debug options.
    
    Args:
        base_handler: Optional base metadata handler
        debug: Enable additional debugging information
    """
    if base_handler is None:
        base_handler = MetadataHandler(debug=debug)
    
    # Validate ExifTool availability
    if not base_handler.exiftool:
        logger.warning("Metadata handler initialized without ExifTool")
```

### Testing

- Add tests for new features
- Ensure tests cover edge cases
- Implement tests for metadata validation
- Test with different ExifTool versions and configurations
- Make sure all tests pass before submitting a pull request

## Metadata Testing Considerations

When testing metadata functionality:

1. Test with various input file types
2. Verify metadata preservation across different conversion modes
3. Check BnF compliance for different document types
4. Validate XML/XMP generation
5. Test error handling for incomplete or malformed metadata

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation if needed
3. The PR should work for Python 3.8 and above
4. Your PR will be reviewed by maintainers, who may request changes

## Acknowledgment

Contributors will be acknowledged in the project README. Thank you for your contributions!

## Questions?

If you have any questions about contributing, please open an issue for discussion.

## License

By contributing to JP2Forge, you agree that your contributions will be licensed under the project's MIT License.

## References

For contributors working on BnF compliance features, please refer to these official BnF documents:

1. BnF Referential (2015): "Référentiel de format de fichier image v2" - [PDF](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)
2. BnF Documentation (2021): "Formats de données pour la préservation à long terme" - [PDF](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

These documents contain the technical specifications that JP2Forge aims to implement for BnF-compliant JPEG2000 conversion.