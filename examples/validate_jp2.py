#!/usr/bin/env python3
"""
Flexible JP2 validation script for JP2Forge.

This script validates one or more JP2 files using JPylyzer integration.
It can handle both single-file and batch (directory) validation.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.tools.tool_manager import ToolManager
from utils.validation import JP2Validator
from utils.logging_config import configure_logging

def validate_files(validator, files, verbose=False, output_dir=None):
    """
    Validate a list of JP2 files and optionally write JSON reports.
    """
    for jp2_file in files:
        print(f"Validating {jp2_file}...")
        result = validator.validate_jp2(str(jp2_file))
        is_valid = result.get("isValid", False)
        print(f"{'✅' if is_valid else '❌'} {os.path.basename(jp2_file)} is {'VALID' if is_valid else 'INVALID'}")
        if verbose:
            print(json.dumps(result, indent=2))
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True, parents=True)
            report_file = output_path / f"{Path(jp2_file).stem}_jpylyzer.json"
            with open(report_file, "w") as f:
                json.dump(result, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Validate JP2 files using JPylyzer integration.")
    parser.add_argument("input", help="JP2 file or directory to validate")
    parser.add_argument("--format", choices=["jp2", "j2c", "jph", "jhc"], default="jp2", help="JPEG2000 format type")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed validation information")
    parser.add_argument("--output", "-o", help="Directory to write JSON validation reports")
    args = parser.parse_args()

    configure_logging(log_level=logging.INFO, verbose=args.verbose)
    tool_manager = ToolManager(prefer_system_tools=True)
    validator = JP2Validator(tool_manager=tool_manager)

    input_path = Path(args.input)
    if input_path.is_file():
        validate_files(validator, [input_path], verbose=args.verbose, output_dir=args.output)
    elif input_path.is_dir():
        files = list(input_path.glob(f"*.{args.format}"))
        if not files:
            print(f"No {args.format} files found in {input_path}")
            return
        validate_files(validator, files, verbose=args.verbose, output_dir=args.output)
    else:
        print(f"Input path not found: {input_path}")

if __name__ == "__main__":
    main()