# Reports Directory

This directory contains analysis reports generated during the JPEG2000 conversion process.

## Contents

Reports include:
- Quality metrics (PSNR, SSIM, MSE)
- Conversion status
- Processing summaries

## Example Usage

Reports are automatically generated when running the workflow with analysis enabled:

```bash
python -m cli.workflow input_dir/ output_dir/ --analyze
```

## File Organization

Files in this directory:
- Report files are named to match their source files
- Reports are stored in CSV and/or JSON format depending on configuration

## Usage Notes

These reports are particularly useful in supervised mode when quality analysis is performed. They are not included in the repository by default.
