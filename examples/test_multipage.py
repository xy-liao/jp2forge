#!/usr/bin/env python3
"""
Test script for multi-page TIFF conversion.

This example demonstrates how to use JP2Forge to process multi-page TIFF files
with different configuration options.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from core.types import WorkflowConfig, DocumentType, CompressionMode, ProcessingMode
from workflow.standard import StandardWorkflow
from utils.logging_config import configure_logging

# Configure logging
configure_logging(log_level=logging.INFO, verbose=True)
logger = logging.getLogger("jp2forge.examples.test_multipage")

def main():
    """Run multi-page TIFF test examples."""
    # Get the path to the input file
    input_dir = Path(__file__).parent.parent / "input_dir"
    output_dir = Path(__file__).parent.parent / "output_dir" / "multipage_test"
    report_dir = Path(__file__).parent.parent / "reports"
    
    # Create output directories if they don't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    # Find the TIFF file in input_dir
    tiff_files = list(input_dir.glob("*.tiff")) + list(input_dir.glob("*.tif"))
    if not tiff_files:
        logger.error("No TIFF files found in input_dir. Please add a TIFF file to test.")
        return
    
    input_file = tiff_files[0]
    logger.info(f"Using input file: {input_file}")
    
    # Example 1: Basic processing with defaults
    logger.info("=== Example 1: Basic Processing with Defaults ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "basic"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(str(input_file))
    print_result(result, "Basic Processing")
    
    # Example 2: Lossless compression
    logger.info("=== Example 2: Lossless Compression ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "lossless"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.LOSSLESS
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(str(input_file))
    print_result(result, "Lossless Compression")
    
    # Example 3: BnF compliant mode
    logger.info("=== Example 3: BnF Compliant Mode ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "bnf"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.BNF_COMPLIANT,
        bnf_compliant=True,
        compression_ratio_tolerance=0.1
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(str(input_file))
    print_result(result, "BnF Compliant")
    
    # Example 4: With custom metadata
    logger.info("=== Example 4: With Custom Metadata ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "metadata"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    workflow = StandardWorkflow(config)
    metadata = {
        "dc:title": "Multi-page Test Document",
        "dc:creator": "JP2Forge Test Suite",
        "dc:rights": "Public Domain",
        "xmp:CreatorTool": "JP2Forge Test Script"
    }
    result = workflow.process_file(str(input_file), metadata=metadata)
    print_result(result, "Custom Metadata")
    
    # Example 5: With overwrite option
    logger.info("=== Example 5: With Overwrite Option ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "overwrite"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED,
        overwrite=True  # Force overwriting existing files
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Run twice to test overwrite
    workflow = StandardWorkflow(config)
    result1 = workflow.process_file(str(input_file))
    logger.info("First run completed, running again with overwrite=True")
    result2 = workflow.process_file(str(input_file))
    print_result(result2, "Overwrite Option")
    
    # Example 6: With skip_existing option
    logger.info("=== Example 6: With Skip Existing Option ===")
    config = WorkflowConfig(
        output_dir=str(output_dir / "skip_existing"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED,
        skip_existing=True  # Skip existing files
    )
    os.makedirs(config.output_dir, exist_ok=True)
    
    # Run twice to test skip_existing
    workflow = StandardWorkflow(config)
    result1 = workflow.process_file(str(input_file))
    logger.info("First run completed, running again with skip_existing=True")
    result2 = workflow.process_file(str(input_file))
    print_result(result2, "Skip Existing Option")
    
    logger.info("All tests completed successfully!")

def print_result(result, label):
    """Print the processing result in a formatted way."""
    print(f"\n----- {label} Result -----")
    print(f"Status: {result.status.name}")
    print(f"Input file: {result.input_file}")
    
    if result.output_file:
        if "," in result.output_file:
            # Multiple output files (multi-page TIFF)
            print(f"Output files: {result.output_file}")
            print(f"Multi-page: Yes")
            if result.file_sizes and 'pages' in result.file_sizes:
                print(f"Pages: {len(result.file_sizes['pages'])}")
                print(f"Total original size: {result.file_sizes.get('original_size_human', 'N/A')}")
                print(f"Total converted size: {result.file_sizes.get('converted_size_human', 'N/A')}")
                print(f"Overall compression ratio: {result.file_sizes.get('compression_ratio', 'N/A')}")
        else:
            # Single output file
            print(f"Output file: {result.output_file}")
            print(f"Multi-page: No")
    
    if result.error:
        print(f"Error: {result.error}")
    
    print("-" * 50)

if __name__ == "__main__":
    main()