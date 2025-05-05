# JP2Forge Quick Start Guide

Welcome to JP2Forge! This guide helps you get started quickly with the essential commands.

## Installation

```bash
# Clone repository
git clone https://github.com/xy-liao/jp2forge.git
cd jp2forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install jpylyzer
```

## Basic Commands

### 1. Convert a Single File

```bash
python -m cli.workflow input.tif output_dir/
```

### 2. Process a Directory

```bash
python -m cli.workflow input_dir/ output_dir/
```

### 3. Use BnF Compliance Mode

```bash
python -m cli.workflow input_dir/ output_dir/ --bnf-compliant
```

### 4. Enable Parallel Processing

```bash
python -m cli.workflow input_dir/ output_dir/ --parallel --max-workers 4
```

## Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--document-type` | Set document type | `--document-type photograph` |
| `--compression-mode` | Set compression mode | `--compression-mode supervised` |
| `--metadata` | Specify metadata file | `--metadata metadata.json` |
| `--verbose` | Enable detailed logging | `--verbose` |
| `--recursive` | Process subdirectories | `--recursive` |

## Example Workflows

### Convert Photos with Quality Control

```bash
python -m cli.workflow photos/ output_dir/ --document-type photograph --compression-mode supervised
```

### Process Historic Documents (BnF Standards)

```bash
python -m cli.workflow documents/ output_dir/ --bnf-compliant --document-type heritage_document
```

### Batch Process with Parallel Execution

```bash
python -m cli.workflow large_collection/ output_dir/ --parallel --max-workers 8 --recursive
```

## Output Location

- Converted JP2 files: `output_dir/`
- Processing reports: `reports/`
- Quality metrics: `reports/metrics/`

## Next Steps

- See the [User Guide](user_guide.md) for detailed instructions
- Learn about [BnF Compliance](NOTATION.md) for archival standards
- Check [Troubleshooting](user_guide.md#11-troubleshooting) for common issues