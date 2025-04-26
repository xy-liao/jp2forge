#!/usr/bin/env python3
"""
Comprehensive test script demonstrating all JP2Forge parameters.

This script shows how to use every available configuration parameter in JP2Forge,
allowing you to see the effects of different settings on the compression process.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from core.types import WorkflowConfig, DocumentType, CompressionMode, ProcessingMode
from workflow.standard import StandardWorkflow
from workflow.parallel import ParallelWorkflow
from utils.logging_config import configure_logging
from utils.profiling import get_profiler

# Configure logging
configure_logging(log_level=logging.INFO, verbose=True)
logger = logging.getLogger("jp2forge.examples.test_all_parameters")


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"=== {title} ===")
    print("=" * 80)


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
            if result.file_sizes:
                print(f"Original size: {result.file_sizes.get('original_size_human', 'N/A')}")
                print(f"Converted size: {result.file_sizes.get('converted_size_human', 'N/A')}")
                print(f"Compression ratio: {result.file_sizes.get('compression_ratio', 'N/A')}")
    
    if result.metrics:
        print("\nQuality Metrics:")
        for key, value in result.metrics.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    
    if result.error:
        print(f"Error: {result.error}")
    
    print("-" * 50)


def run_test(config, input_file, test_name):
    """Run a test with the given configuration."""
    # Determine the workflow type based on the processing mode
    if config.processing_mode == ProcessingMode.PARALLEL:
        workflow = ParallelWorkflow(config)
    else:
        workflow = StandardWorkflow(config)
    
    # Record start time for performance measurement
    start_time = time.time()
    
    # Process the file
    result = workflow.process_file(str(input_file))
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print(f"\nProcessing time: {elapsed_time:.2f} seconds")
    
    print_result(result, test_name)
    return result


def main():
    """Run comprehensive tests with all parameters."""
    # Setup input/output directories
    input_dir = Path(__file__).parent.parent / "input_dir"
    output_base = Path(__file__).parent.parent / "output_dir" / "test_params"
    report_dir = output_base / "reports"
    
    # Create output directories
    os.makedirs(output_base, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    
    # Find test files
    tiff_files = list(input_dir.glob("*.tiff")) + list(input_dir.glob("*.tif"))
    if not tiff_files:
        logger.error("No TIFF files found in input_dir. Please add TIFF files to test.")
        return
    
    input_file = tiff_files[0]
    logger.info(f"Using input file: {input_file}")
    
    # 1. Basic test with default settings
    print_section("1. Default Settings")
    default_config = WorkflowConfig(
        output_dir=str(output_base / "default"),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED
    )
    os.makedirs(default_config.output_dir, exist_ok=True)
    run_test(default_config, input_file, "Default Settings")
    
    # 2. Test all document types
    print_section("2. Document Types")
    for doc_type in DocumentType:
        doc_type_dir = output_base / f"doc_type_{doc_type.name.lower()}"
        os.makedirs(doc_type_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(doc_type_dir),
            report_dir=str(report_dir),
            document_type=doc_type,
            compression_mode=CompressionMode.SUPERVISED
        )
        run_test(config, input_file, f"Document Type: {doc_type.name}")
    
    # 3. Test all compression modes
    print_section("3. Compression Modes")
    for comp_mode in CompressionMode:
        comp_mode_dir = output_base / f"comp_mode_{comp_mode.value}"
        os.makedirs(comp_mode_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(comp_mode_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=comp_mode
        )
        run_test(config, input_file, f"Compression Mode: {comp_mode.value}")
    
    # 4. Test different quality thresholds
    print_section("4. Quality Thresholds")
    for quality in [30.0, 35.0, 40.0, 45.0, 50.0]:
        quality_dir = output_base / f"quality_{quality:.1f}"
        os.makedirs(quality_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(quality_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            quality_threshold=quality
        )
        run_test(config, input_file, f"Quality Threshold: {quality}")
    
    # 5. Test different resolution levels
    print_section("5. Resolution Levels")
    for resolutions in [5, 8, 10, 12]:
        resolution_dir = output_base / f"resolutions_{resolutions}"
        os.makedirs(resolution_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(resolution_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            num_resolutions=resolutions
        )
        run_test(config, input_file, f"Resolution Levels: {resolutions}")
    
    # 6. Test different progression orders
    print_section("6. Progression Orders")
    for prog_order in ["LRCP", "RLCP", "RPCL", "PCRL", "CPRL"]:
        prog_order_dir = output_base / f"prog_order_{prog_order}"
        os.makedirs(prog_order_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(prog_order_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            progression_order=prog_order
        )
        run_test(config, input_file, f"Progression Order: {prog_order}")
    
    # 7. Test processing modes
    print_section("7. Processing Modes")
    for proc_mode in ProcessingMode:
        proc_mode_dir = output_base / f"proc_mode_{proc_mode.name.lower()}"
        os.makedirs(proc_mode_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(proc_mode_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            processing_mode=proc_mode,
            max_workers=2 if proc_mode == ProcessingMode.PARALLEL else None
        )
        run_test(config, input_file, f"Processing Mode: {proc_mode.name}")
    
    # 8. Test chunk sizes for large image handling
    print_section("8. Chunk Sizes")
    for chunk_size in [500000, 1000000, 2000000]:
        chunk_dir = output_base / f"chunk_{chunk_size}"
        os.makedirs(chunk_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(chunk_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            chunk_size=chunk_size
        )
        run_test(config, input_file, f"Chunk Size: {chunk_size}")
    
    # 9. Test memory limits
    print_section("9. Memory Limits")
    for memory_limit in [1024, 2048, 4096]:
        memory_dir = output_base / f"memory_{memory_limit}mb"
        os.makedirs(memory_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(memory_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            memory_limit_mb=memory_limit
        )
        run_test(config, input_file, f"Memory Limit: {memory_limit}MB")
    
    # 10. Test adaptive workers
    print_section("10. Adaptive Workers")
    adaptive_dir = output_base / "adaptive_workers"
    os.makedirs(adaptive_dir, exist_ok=True)
    
    config = WorkflowConfig(
        output_dir=str(adaptive_dir),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED,
        processing_mode=ProcessingMode.PARALLEL,
        adaptive_workers=True,
        min_workers=1,
        memory_threshold=0.8,
        cpu_threshold=0.9,
        max_workers=4
    )
    run_test(config, input_file, "Adaptive Workers")
    
    # 11. Test BnF compliant mode with different tolerances
    print_section("11. BnF Compliant Options")
    for tolerance in [0.05, 0.1, 0.2]:
        bnf_dir = output_base / f"bnf_tolerance_{tolerance:.2f}"
        os.makedirs(bnf_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(bnf_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.BNF_COMPLIANT,
            bnf_compliant=True,
            compression_ratio_tolerance=tolerance,
            include_bnf_markers=True
        )
        run_test(config, input_file, f"BnF Compliance (Tolerance: {tolerance})")
    
    # 12. Test memory pool options
    print_section("12. Memory Pool Options")
    memory_pool_dir = output_base / "memory_pool"
    os.makedirs(memory_pool_dir, exist_ok=True)
    
    config = WorkflowConfig(
        output_dir=str(memory_pool_dir),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED,
        use_memory_pool=True,
        memory_pool_size_mb=50,
        memory_pool_max_blocks=8
    )
    run_test(config, input_file, "Memory Pooling Enabled")
    
    # 13. Test profiling options
    print_section("13. Profiling Options")
    profiling_dir = output_base / "profiling"
    os.makedirs(profiling_dir, exist_ok=True)
    
    # Initialize the profiler with memory tracking enabled
    profiler = get_profiler(
        output_dir=str(report_dir),
        enabled=True,
        track_memory=True,
        detailed_memory=True
    )
    
    config = WorkflowConfig(
        output_dir=str(profiling_dir),
        report_dir=str(report_dir),
        document_type=DocumentType.PHOTOGRAPH,
        compression_mode=CompressionMode.SUPERVISED,
        enable_profiling=True,
        detailed_memory_tracking=True
    )
    run_test(config, input_file, "With Profiling")
    
    # 14. Test target compression ratio
    print_section("14. Target Compression Ratio")
    for ratio in [10.0, 20.0, 30.0]:
        ratio_dir = output_base / f"target_ratio_{ratio:.1f}"
        os.makedirs(ratio_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(ratio_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            target_compression_ratio=ratio
        )
        run_test(config, input_file, f"Target Compression Ratio: {ratio}:1")
    
    # 15. Test target size
    print_section("15. Target Size")
    # Calculate approximate target sizes based on the original file size
    original_size = os.path.getsize(input_file)
    for size_factor in [0.1, 0.25, 0.5]:
        target_size = int(original_size * size_factor)
        size_dir = output_base / f"target_size_{target_size}"
        os.makedirs(size_dir, exist_ok=True)
        
        config = WorkflowConfig(
            output_dir=str(size_dir),
            report_dir=str(report_dir),
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            target_size=target_size
        )
        run_test(config, input_file, f"Target Size: {target_size} bytes ({size_factor*100}% of original)")
    
    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    main()