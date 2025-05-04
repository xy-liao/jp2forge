#!/usr/bin/env python3
"""
JP2Forge Workflow CLI

Command-line interface for the JP2Forge workflow, supporting both
sequential and parallel processing modes.
"""

import os
import sys
import json
import logging
import argparse
from utils.logging_config import configure_logging
import traceback
import multiprocessing
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.types import (
    DocumentType,
    CompressionMode,
    ProcessingMode,
    WorkflowStatus,
    WorkflowConfig
)
from workflow.standard import StandardWorkflow
from workflow.parallel import ParallelWorkflow
from utils.validation import JP2Validator

# Setup logger
logger = logging.getLogger("jp2forge")


def create_workflow(config: WorkflowConfig):
    """Create the appropriate workflow based on configuration.

    Args:
        config: Workflow configuration

    Returns:
        Workflow instance
    """
    if config.processing_mode == ProcessingMode.PARALLEL:
        return ParallelWorkflow(config)
    else:
        return StandardWorkflow(config)


def validate_output_with_jpylyzer(output_dir, report_dir):
    """
    Validate all JP2 files in output_dir using JPylyzer and write a single JSON report to report_dir.
    """
    validator = JP2Validator()
    output_path = Path(output_dir)
    report_path = Path(report_dir)
    report_path.mkdir(exist_ok=True, parents=True)

    all_results = {}
    for jp2_file in output_path.glob("*.jp2"):
        result = validator.validate_jp2(str(jp2_file))
        all_results[jp2_file.name] = result
    # Write a single JSON file with all results
    summary_file = report_path / "info_jpylyzer.json"
    with open(summary_file, "w") as f:
        json.dump(all_results, f, indent=2)


def generate_summary_report_with_jpylyzer(results, config, report_dir):
    """
    Generate summary_report.md using only info_jpylyzer.json for validation status.
    """
    info_jpylyzer_path = Path(report_dir) / "info_jpylyzer.json"
    if not info_jpylyzer_path.exists():
        logger.warning("info_jpylyzer.json not found, skipping summary report generation.")
        return
    with open(info_jpylyzer_path, "r") as f:
        jpylyzer_data = json.load(f)

    # Calculate statistics if they aren't already present
    total_files = len(results.get('processed_files', []))
    success_count = results.get('success_count', 0)
    if 'success_count' not in results:
        # Calculate successful files if not provided
        success_count = sum(1 for file in results.get('processed_files', [])
                            if file.get('status') == 'SUCCESS')
        results['success_count'] = success_count

    warning_count = results.get('warning_count', 0)
    error_count = results.get('error_count', 0)
    corrupted_count = results.get('corrupted_count', 0)

    # Use .name if status is an enum, otherwise use the string value directly with 'UNKNOWN' as fallback
    overall_status = results.get('status', 'UNKNOWN')
    if hasattr(overall_status, 'name'):
        overall_status = overall_status.name

    summary_lines = []
    summary_lines.append("# JPEG2000 Conversion Summary Report")
    summary_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    summary_lines.append("## Overall Statistics\n-----------------")
    summary_lines.append(f"Total Files: {total_files}")
    summary_lines.append(f"Successful: {success_count}")
    summary_lines.append(f"Warnings: {warning_count}")
    summary_lines.append(f"Errors: {error_count}")
    summary_lines.append(f"Corrupted: {corrupted_count}")
    summary_lines.append(f"Overall Status: {overall_status}")

    if results.get('processing_time', 0) > 0:
        summary_lines.append(f"Total Processing Time: {results['processing_time']:.2f} seconds")
        if total_files > 0:
            summary_lines.append(
                f"Average Processing Rate: {total_files / results['processing_time']:.2f} files/second\n")

    summary_lines.append("## Configuration\n-----------------")
    for key, value in config.items():
        summary_lines.append(f"{key}: {value}")
    summary_lines.append("")
    summary_lines.append("## Detailed Results\n----------------")

    for file_result in results.get('processed_files', []):
        input_file = file_result.get('input_file', 'Unknown')
        status = file_result.get('status', 'UNKNOWN')
        output_file = file_result.get('output_file', '')
        orig_size = file_result.get('file_sizes', {}).get('original_size_human', 'N/A')
        conv_size = file_result.get('file_sizes', {}).get('converted_size_human', 'N/A')
        ratio = file_result.get('file_sizes', {}).get('compression_ratio', 'N/A')
        jp2_name = Path(output_file).name if output_file else ''
        is_valid = jpylyzer_data.get(jp2_name, {}).get('isValid', None)

        summary_lines.append(f"File: {input_file}")
        summary_lines.append(f"Status: {status}")
        summary_lines.append(f"Output: {output_file}")
        summary_lines.append(f"Original Size: {orig_size}")
        summary_lines.append(f"Converted Size: {conv_size}")
        summary_lines.append(f"Compression Ratio: {ratio}")
        summary_lines.append(f"Jpylyzer Validation: {is_valid}")
        summary_lines.append("")

    with open(Path(report_dir) / "summary_report.md", "w") as f:
        f.write("\n".join(summary_lines))

    logger.info(
        f"Summary report with Jpylyzer validation written to: {Path(report_dir) / 'summary_report.md'}")


def main():
    """Main entry point for the JP2Forge workflow CLI."""
    parser = argparse.ArgumentParser(
        description="JPEG2000 conversion and analysis workflow"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit"
    )
    parser.add_argument(
        "input_path",
        nargs="?",  # Make input_path optional when --version is used
        help="Path to input TIFF file or directory"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",  # Make output_dir optional when --version is used
        help="Directory for converted JPEG2000 files"
    )
    parser.add_argument(
        "--document-type",
        choices=[dt.name.lower() for dt in DocumentType],
        default=DocumentType.PHOTOGRAPH.name.lower(),
        help="Type of document being processed"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        help="Path to log file"
    )
    parser.add_argument(
        "--logfile",
        dest="log_file",
        help="Path to log file (alias for --log-file)"
    )
    parser.add_argument(
        "--loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    parser.add_argument(
        "--debug",
        action="store_const",
        const="DEBUG",
        dest="loglevel",
        help="Enable debug mode (shorthand for --loglevel=DEBUG)"
    )
    parser.add_argument(
        "--report-dir",
        default="reports",
        help="Directory for analysis reports"
    )
    parser.add_argument(
        "--quality",
        type=float,
        default=40.0,
        help="Quality threshold for compression (PSNR)"
    )
    parser.add_argument(
        "--resolutions",
        type=int,
        default=10,
        help="Number of resolution levels"
    )
    parser.add_argument(
        "--progression",
        default="RPCL",
        help="Progression order for JPEG2000"
    )
    parser.add_argument(
        "--compression-mode",
        choices=[mode.value for mode in CompressionMode],
        default=CompressionMode.SUPERVISED.value,
        help="Compression mode to use"
    )
    parser.add_argument(
        "--bnf-compliant",
        action="store_true",
        help="Use BnF compliant settings"
    )
    parser.add_argument(
        "--compression-ratio-tolerance",
        type=float,
        default=0.05,
        help="Tolerance for compression ratio (default: 0.05 or 5%%)"
    )
    parser.add_argument(
        "--compression-ratio",
        type=float,
        help="Target compression ratio (e.g., 20 for 20:1 compression)"
    )
    parser.add_argument(
        "--target-size",
        type=int,
        help="Target size in bytes for compressed images"
    )
    parser.add_argument(
        "--include-bnf-markers",
        action="store_true",
        default=True,
        help="Include BnF robustness markers (SOP, EPH, PLT)"
    )
    parser.add_argument(
        "--use-kakadu",
        action="store_true",
        help="Use Kakadu (if available) for BnF compliant conversion"
    )
    parser.add_argument(
        "--kakadu-path",
        default="kdu_compress",
        help="Path to Kakadu executable"
    )
    parser.add_argument(
        "--no-lossless-fallback",
        action="store_true",
        help="Disable fallback to lossless compression"
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Process subdirectories recursively"
    )
    parser.add_argument(
        "--metadata",
        help="Path to JSON file containing metadata"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Use parallel processing"
    )
    parser.add_argument(
        "--threads",
        type=int,
        dest="max_workers",
        help="Number of threads to use (alias for --max-workers)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=None,
        help="Maximum number of worker processes (default: %(default)s)"
    )
    parser.add_argument(
        "--adaptive-workers",
        action="store_true",
        help="Enable adaptive worker pool scaling based on system resources"
    )
    parser.add_argument(
        "--min-workers",
        type=int,
        default=1,
        help="Minimum number of worker processes for adaptive scaling (default: 1)"
    )
    parser.add_argument(
        "--memory-threshold",
        type=float,
        default=0.8,
        help="Memory usage threshold (0-1) for adaptive scaling (default: 0.8)"
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=0.9,
        help="CPU usage threshold (0-1) for adaptive scaling (default: 0.9)"
    )
    parser.add_argument(
        "--memory-limit",
        type=int,
        default=4096,
        help="Memory limit in MB for adaptive processing (default: 4096)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000000,
        help="Number of pixels to process at once for large images (default: 1000000)"
    )
    parser.add_argument(
        "--no-compression",
        action="store_true",
        help="Skip compression step (for debugging)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode for error handling"
    )
    parser.add_argument(
        "--no-upscale",
        action="store_true",
        help="Don't upscale images to minimum dimensions"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip existing files"
    )
    parser.add_argument(
        "--collector-batch-size",
        type=int,
        default=10,
        help="Number of files to process in a batch"
    )
    parser.add_argument(
        "--collector-threads",
        type=int,
        default=1,
        help="Number of threads to use for collection"
    )
    parser.add_argument(
        "--converter-threads",
        type=int,
        default=None,
        help="Number of threads to use for conversion"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--save-config",
        help="Save configuration to JSON file"
    )

    args = parser.parse_args()

    # Handle version flag
    if args.version:
        import pkg_resources
        try:
            version = pkg_resources.get_distribution("jp2forge").version
        except pkg_resources.DistributionNotFound:
            version = "0.9.1"  # Default version if not installed as package
        print(f"JP2Forge version {version}")
        return 0

    # Configure logging
    log_level = getattr(logging, args.loglevel.upper(), logging.INFO)
    configure_logging(
        log_level=log_level,
        log_file=args.log_file,
        verbose=args.verbose
    )

    # Header information
    logger.info("=" * 80)
    logger.info("JP2Forge Workflow")
    logger.info("=" * 80)

    # Create workflow configuration
    if args.config and os.path.exists(args.config):
        # Load configuration from file
        try:
            with open(args.config, 'r') as f:
                config_dict = json.load(f)
            config = WorkflowConfig.from_dict(config_dict)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return 1
    else:
        # Create configuration from command-line arguments
        config = WorkflowConfig(
            output_dir=args.output_dir,
            report_dir=args.report_dir,
            document_type=DocumentType[args.document_type.upper()],
            quality_threshold=args.quality,
            num_resolutions=args.resolutions,
            progression_order=args.progression,
            compression_mode=(CompressionMode.BNF_COMPLIANT
                              if args.bnf_compliant and args.compression_mode != "lossless"
                              else CompressionMode(args.compression_mode)),
            processing_mode=ProcessingMode.PARALLEL if args.parallel else ProcessingMode.SEQUENTIAL,
            max_workers=args.max_workers,
            memory_limit_mb=args.memory_limit,
            adaptive_workers=args.adaptive_workers,
            min_workers=args.min_workers,
            memory_threshold=args.memory_threshold,
            cpu_threshold=args.cpu_threshold,
            chunk_size=args.chunk_size,
            lossless_fallback=not args.no_lossless_fallback,
            verbose=args.verbose,
            recursive=args.recursive,
            bnf_compliant=args.bnf_compliant,
            compression_ratio_tolerance=args.compression_ratio_tolerance,
            include_bnf_markers=args.include_bnf_markers,
            no_compression=args.no_compression,
            strict=args.strict,
            no_upscale=args.no_upscale,
            keep_temp=args.keep_temp,
            overwrite=args.overwrite,
            skip_existing=args.skip_existing,
            collector_batch_size=args.collector_batch_size,
            collector_threads=args.collector_threads,
            converter_threads=args.converter_threads or args.max_workers,
            target_compression_ratio=args.compression_ratio,
            target_size=args.target_size
        )

    # Save configuration if requested
    if args.save_config:
        try:
            save_dir = os.path.dirname(args.save_config)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            with open(args.save_config, 'w') as f:
                json.dump(config.to_dict(), f, indent=4)
            logger.info(f"Saved configuration to {args.save_config}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")

    # Log configuration
    logger.info(f"Processing: {args.input_path}")
    logger.info(f"Output directory: {config.output_dir}")
    logger.info(f"Document type: {config.document_type.name}")
    logger.info(f"Compression mode: {config.compression_mode.value}")
    logger.info(f"Processing mode: {config.processing_mode.name}")
    if config.processing_mode == ProcessingMode.PARALLEL:
        logger.info(
            f"Using {config.max_workers or (multiprocessing.cpu_count() - 1)} worker processes")
    logger.info("-" * 80)

    # Create the workflow
    # Initialize the compressor with Kakadu if requested
    use_kakadu = args.bnf_compliant and args.use_kakadu

    # Create the workflow
    workflow = create_workflow(config)

    # Set Kakadu parameters if used
    if use_kakadu and hasattr(workflow, 'compressor'):
        workflow.compressor.use_kakadu = True
        workflow.compressor.kakadu_path = args.kakadu_path

    # Load metadata if provided
    metadata = None
    if args.metadata and os.path.exists(args.metadata):
        try:
            with open(args.metadata, 'r') as f:
                metadata = json.load(f)
            logger.info(f"Loaded metadata from {args.metadata}")
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")

    # Process input
    if os.path.isfile(args.input_path):
        # Process single file
        logger.info(f"Processing single file: {args.input_path}")

        result = workflow.process_file(args.input_path)
        
        # Create a results dictionary similar to what process_directory returns
        single_file_results = {
            'status': result.status,
            'processed_files': [{
                'input_file': args.input_path,
                'output_file': result.output_file,
                'status': result.status.name,
                'file_sizes': {
                    'original_size_human': f"{os.path.getsize(args.input_path) / (1024 * 1024):.2f} MB" if os.path.exists(args.input_path) else "N/A",
                    'converted_size_human': f"{os.path.getsize(result.output_file) / (1024 * 1024):.2f} MB" if result.output_file and os.path.exists(result.output_file) else "N/A",
                    'compression_ratio': os.path.getsize(args.input_path) / os.path.getsize(result.output_file) if result.output_file and os.path.exists(result.output_file) and os.path.getsize(result.output_file) > 0 else "N/A"
                }
            }],
            'success_count': 1 if result.status != WorkflowStatus.FAILURE else 0,
            'warning_count': 0,  # You may want to calculate this based on result
            'error_count': 1 if result.status == WorkflowStatus.FAILURE else 0,
            'processing_time': result.processing_time if hasattr(result, 'processing_time') else 0
        }
        
        # Generate validation and reports just like in directory processing
        validate_output_with_jpylyzer(args.output_dir, args.report_dir)
        generate_summary_report_with_jpylyzer(single_file_results, config.to_dict(), args.report_dir)

        logger.info("-" * 80)
        logger.info(f"Processing status: {result.status.name}")

        if result.output_file:
            orig_size = os.path.getsize(args.input_path) / (1024 * 1024)
            new_size = os.path.getsize(result.output_file) / (1024 * 1024)
            compression_ratio = orig_size / new_size if new_size > 0 else 0

            logger.info(f"Original size: {orig_size:.2f} MB")
            logger.info(f"Compressed size: {new_size:.2f} MB")
            logger.info(f"Achieved compression ratio: {compression_ratio:.2f}:1")

        if result.report_file:
            logger.info(f"Report file: {result.report_file}")

        if result.error:
            logger.error(f"Error: {result.error}")
            return 1

        return 0 if result.status != WorkflowStatus.FAILURE else 1

    else:
        # Process directory
        logger.info(f"Processing directory: {args.input_path}")
        if args.recursive:
            logger.info("Processing subdirectories recursively")

        results = workflow.process_directory(
            args.input_path,
            metadata=metadata
        )
        # JPylyzer validation and reporting
        validate_output_with_jpylyzer(args.output_dir, args.report_dir)
        logger.info(f"JPylyzer validation reports written to: {args.report_dir}")

        # Generate summary report
        generate_summary_report_with_jpylyzer(results, config.to_dict(), args.report_dir)

        logger.info("-" * 80)
        logger.info(f"Processing status: {results['status'].name}")

        # Handle the case when directory processing fails
        if 'error' in results:
            logger.error(f"Error: {results['error']}")
            return 1

        # Only access these keys if directory processing was successful
        logger.info(f"Files processed: {len(results.get('processed_files', []))}")
        logger.info(f"Successful: {results.get('success_count', 0)}")
        logger.info(f"Warnings: {results.get('warning_count', 0)}")
        logger.info(f"Errors: {results.get('error_count', 0)}")

        if 'processing_time' in results:
            logger.info(f"Processing time: {results['processing_time']:.2f} seconds")
            if results['processing_time'] > 0 and len(results.get('processed_files', [])) > 0:
                logger.info(
                    f"Processing rate: {len(results['processed_files']) / results['processing_time']:.2f} files/second")

        if results.get('summary_report'):
            logger.info(f"Summary report: {results['summary_report']}")

        logger.info("=" * 80)
        logger.info("Processing complete")
        logger.info("=" * 80)

        return 0 if results['status'] != WorkflowStatus.FAILURE else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)
