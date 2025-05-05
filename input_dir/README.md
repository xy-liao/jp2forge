# Input Directory

This directory contains source TIFF files for processing with jp2forge.

## Contents

This directory should contain image files that will be processed and converted to JPEG2000 format:
- TIFF files (.tif, .tiff)
- Other supported image formats depending on configuration

## Example Usage

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

## File Organization

Files placed in this directory can be:
- Single or multi-page TIFF files
- Organized in subdirectories (the directory structure will be preserved in output)
- Named according to your project's conventions

## Usage Notes

- Input files should be in formats supported by jp2forge (primarily TIFF)
- Current sample files may vary (e.g., Arkansas Constitution pages)
- You can add your own test images to this directory for conversion
- Large files may require additional memory resources

## Sample Commands

Process all files in the input directory:
```bash
python -m cli.workflow input_dir/ output_dir/
```

Process with specific quality settings:
```bash
python -m cli.workflow input_dir/ output_dir/ --quality high
```
