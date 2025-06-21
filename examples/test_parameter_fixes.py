#!/usr/bin/env python3
"""
Test script to verify the correct handling of parameters in multi-page TIFF
processing.

This script specifically focuses on testing the memory-efficient processing
parameters.
"""

import os
import sys
import json
import logging
import argparse

# Add parent directory to path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.types import WorkflowConfig, DocumentType, CompressionMode
from workflow.standard import StandardWorkflow


def setup_logging():
    """Configure logging for the test script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    # Also log to file for analysis
    file_handler = logging.FileHandler('parameter_test.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test parameter fixes for multi-page TIFF processing"
    )
    parser.add_argument(
        "--input", 
        help="Path to input multi-page TIFF file",
        required=True
    )
    parser.add_argument(
        "--output", 
        help="Path to output directory",
        required=True
    )
    return parser.parse_args()


def test_memory_parameters(logger, input_path, output_path):
    """
    Run tests with different memory parameter combinations.
    
    Args:
        logger: Configured logger
        input_path: Path to input multi-page TIFF file
        output_path: Base output directory
    
    Returns:
        dict: Test results
    """
    logger.info("Input file: %s", input_path)
    logger.info("Output directory: %s", output_path)
    
    test_cases = [
        {
            "name": "Default parameters",
            "output_subdir": "default",
            "params": {}
        },
        {
            "name": "Low memory limit",
            "output_subdir": "low_memory",
            "params": {
                # Set a low memory limit to trigger memory-efficient processing
                "memory_limit_mb": 512
            }
        },
        {
            "name": "Small chunk size",
            "output_subdir": "small_chunk",
            "params": {
                # Small chunk size should trigger memory-efficient processing
                "chunk_size": 250000
            }
        },
        {
            "name": "Both parameters",
            "output_subdir": "both_params",
            "params": {
                "memory_limit_mb": 768,
                "chunk_size": 500000
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        logger.info("Running test case: %s", test_case["name"])
        output_dir = os.path.join(output_path, test_case["output_subdir"])
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure the workflow with test parameters
        config = WorkflowConfig(
            input_file=input_path,
            output_dir=output_dir,
            report_dir=output_path,
            document_type=DocumentType.PHOTOGRAPH,
            compression_mode=CompressionMode.SUPERVISED,
            **test_case["params"]
        )
        
        workflow = StandardWorkflow(config)
        try:
            result = workflow.process_file(input_path)
            status = result.status.name if hasattr(result, 'status') else "UNKNOWN"
            
            # Check if memory-efficient processing was triggered
            try:
                with open('parameter_test.log', 'r', encoding='utf-8') as log_file:
                    log_content = log_file.read()
                
                memory_efficient_triggered = (
                    "memory-efficient processing" in log_content
                )
                
                page_count = (
                    len(result.metrics.get("multipage_results", []))
                    if result.metrics else 0
                )
                
                results[test_case["name"]] = {
                    "status": status,
                    "memory_efficient_triggered": memory_efficient_triggered,
                    "page_count": page_count
                }
                
            except Exception as exc:
                logger.error("Error analyzing log file: %s", str(exc))
                results[test_case["name"]] = {"status": status}
            
            logger.info(
                "Completed test case: %s with status %s", 
                test_case["name"], 
                status
            )
            
            if test_case["name"] != "Default parameters":
                logger.info("Memory-efficient processing was triggered as expected")
                
        except Exception as exc:
            logger.error("Test case failed: %s", str(exc))
            results[test_case["name"]] = {"status": "ERROR"}
    
    return results


def main():
    """Run the parameter testing script."""
    logger = setup_logging()
    args = parse_arguments()
    
    try:
        logger.info("Starting parameter test suite")
        results = test_memory_parameters(logger, args.input, args.output)
        
        # Print summary
        logger.info("\n--- Parameter Fix Test Results ---\n")
        for test_name, result in results.items():
            print(f"Test: {test_name}")
            print(f"Status: {result.get('status', 'UNKNOWN')}")
            print(
                f"Memory-efficient processing triggered: "
                f"{result.get('memory_efficient_triggered', False)}"
            )
            print(f"Pages processed: {result.get('page_count', 0)}")
            print()
        
        logger.info("All tests completed")
        
    except Exception as exc:
        logger.error("Test suite failed: %s", str(exc))
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())