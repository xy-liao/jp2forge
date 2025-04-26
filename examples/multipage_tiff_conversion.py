#!/usr/bin/env python3
"""
Comprehensive example demonstrating multi-page TIFF processing with JP2Forge.

This script shows various options and configurations for processing multi-page TIFF files,
including basic conversion, metadata handling, BnF compliance, and memory optimization.

Example usage:
    python multipage_tiff_conversion.py --input input_dir/multipage.tiff --output output_dir/ --mode basic
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import JP2Forge modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('multipage_conversion.log')
        ]
    )

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Multi-page TIFF processing example")
    parser.add_argument("--input", required=True, help="Input TIFF file or directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--mode", choices=["basic", "bnf", "lossless", "memory", "metadata"],
                        default="basic", help="Processing mode to demonstrate")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    return parser.parse_args()

def run_basic_conversion(input_path, output_path):
    """Run basic multi-page TIFF conversion."""
    print("Running basic multi-page TIFF conversion...")
    
    # Create a basic configuration
    config = WorkflowConfig(
        output_dir=output_path,
        compression_mode=CompressionMode.SUPERVISED,
        document_type=DocumentType.PHOTOGRAPH,
        quality_threshold=40.0,
        skip_existing=False,  # Process all pages, even if output files exist
        overwrite=True        # Overwrite existing files
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(input_path)
    
    print(f"Basic conversion completed with status: {result.status.name}")
    print(f"Output files: {result.output_file}")
    return result

def run_bnf_conversion(input_path, output_path):
    """Run BnF-compliant multi-page TIFF conversion."""
    print("Running BnF-compliant multi-page TIFF conversion...")
    
    # Create BnF-compliant configuration
    config = WorkflowConfig(
        output_dir=output_path,
        compression_mode=CompressionMode.BNF_COMPLIANT,
        document_type=DocumentType.HERITAGE_DOCUMENT,  # Uses 1:4 ratio for BnF
        bnf_compliant=True,
        compression_ratio_tolerance=0.05,  # 5% tolerance
        num_resolutions=10,                # BnF recommends 10
        quality_layers=10,                 # BnF recommends 10
        progression_order="RPCL",          # BnF standard
        include_bnf_markers=True           # Add SOP, EPH markers when possible
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(input_path)
    
    print(f"BnF-compliant conversion completed with status: {result.status.name}")
    print(f"Compression ratio: {result.file_sizes.get('compression_ratio', 'N/A')}")
    return result

def run_lossless_conversion(input_path, output_path):
    """Run lossless multi-page TIFF conversion."""
    print("Running lossless multi-page TIFF conversion...")
    
    # Create lossless configuration
    config = WorkflowConfig(
        output_dir=output_path,
        compression_mode=CompressionMode.LOSSLESS,
        document_type=DocumentType.PHOTOGRAPH,
        num_resolutions=8,  # More resolution levels for better zooming
        skip_existing=True  # Skip files that already exist
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(input_path)
    
    print(f"Lossless conversion completed with status: {result.status.name}")
    if result.file_sizes:
        print(f"Original size: {result.file_sizes.get('original_size_human', 'N/A')}")
        print(f"Converted size: {result.file_sizes.get('converted_size_human', 'N/A')}")
    return result

def run_memory_optimized_conversion(input_path, output_path):
    """Run memory-optimized multi-page TIFF conversion for large files."""
    print("Running memory-optimized multi-page TIFF conversion...")
    
    # Create memory-optimized configuration
    config = WorkflowConfig(
        output_dir=output_path,
        compression_mode=CompressionMode.SUPERVISED,
        document_type=DocumentType.PHOTOGRAPH,
        memory_limit_mb=1024,      # Limit memory usage to 1GB
        min_chunk_height=32,       # Small chunks for memory efficiency
        chunk_size=500000,         # Process in small chunks (500K pixels)
        use_memory_mapping=True    # Use memory-mapped files for efficiency
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(input_path)
    
    print(f"Memory-optimized conversion completed with status: {result.status.name}")
    print(f"Pages processed: {len(result.metrics.get('multipage_results', []))}")
    return result

def run_metadata_conversion(input_path, output_path):
    """Run multi-page TIFF conversion with custom metadata."""
    print("Running multi-page TIFF conversion with custom metadata...")
    
    # Example metadata (similar to BnF format)
    metadata = {
        "dcterms:isPartOf": "TEST_DOCUMENT",
        "dcterms:provenance": "JP2Forge Example",
        "dc:creator": "JP2Forge User",
        "dc:description": "Multi-page TIFF example conversion",
        "tiff:Make": "Test Scanner",
        "tiff:Model": "Scanner 2000",
        "xmp:CreatorTool": "JP2Forge Example Script",
        "xmp:CreateDate": "2025-04-25T10:30:00Z"
    }
    
    # Create configuration with metadata
    config = WorkflowConfig(
        output_dir=output_path,
        compression_mode=CompressionMode.SUPERVISED,
        document_type=DocumentType.PHOTOGRAPH,
        quality_threshold=40.0
    )
    
    workflow = StandardWorkflow(config)
    result = workflow.process_file(input_path, metadata=metadata)
    
    print(f"Metadata conversion completed with status: {result.status.name}")
    print(f"Metadata applied to all {len(result.metrics.get('multipage_results', []))} pages")
    return result

def main():
    """Main function to run the example."""
    setup_logging()
    args = parse_arguments()
    
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Run the selected mode
    if args.mode == "basic":
        result = run_basic_conversion(input_path, output_path)
    elif args.mode == "bnf":
        result = run_bnf_conversion(input_path, output_path)
    elif args.mode == "lossless":
        result = run_lossless_conversion(input_path, output_path)
    elif args.mode == "memory":
        result = run_memory_optimized_conversion(input_path, output_path)
    elif args.mode == "metadata":
        result = run_metadata_conversion(input_path, output_path)
    else:
        print(f"Unknown mode: {args.mode}")
        return

    # Print summary report
    print("\n--- Multi-page TIFF Processing Summary ---")
    print(f"Input file: {input_path}")
    print(f"Output directory: {output_path}")
    print(f"Status: {result.status.name}")
    
    # Show page-specific information if available
    if "multipage_results" in result.metrics:
        pages = result.metrics["multipage_results"]
        print(f"Total pages processed: {len(pages)}")
        
        # Count successes and failures
        successes = sum(1 for page in pages if page.get("status") == "SUCCESS")
        failures = sum(1 for page in pages if page.get("status") == "FAILURE")
        
        print(f"Successful pages: {successes}")
        print(f"Failed pages: {failures}")

if __name__ == "__main__":
    main()