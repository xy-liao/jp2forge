"""
Shared utilities for workflow implementations.

This module contains common functions and utilities used by both
StandardWorkflow and ParallelWorkflow to avoid code duplication.
"""

import os
from typing import Dict, Any


def format_file_size(size_in_bytes):
    """Format file size in a human-readable format.

    Args:
        size_in_bytes: Size in bytes

    Returns:
        String with human-readable file size
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 * 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 * 1024 * 1024):.2f} GB"


def _calculate_file_sizes(result, input_file):
    """Calculate and format file sizes for processing result.
    
    Args:
        result: ProcessingResult object
        input_file: Path to input file
        
    Returns:
        Dictionary with file size information
    """
    file_sizes = {}
    if hasattr(result, 'file_sizes') and result.file_sizes:
        file_sizes = result.file_sizes
    elif result.output_file and os.path.exists(result.output_file) and os.path.exists(input_file):
        # Calculate file sizes if not available but files exist
        original_size = os.path.getsize(input_file)
        converted_size = os.path.getsize(result.output_file)

        # Format sizes into human-readable format
        original_size_human = format_file_size(original_size)
        converted_size_human = format_file_size(converted_size)

        # Calculate compression ratio
        compression_ratio = f"{original_size / converted_size:.2f}:1" if converted_size > 0 else "N/A"

        file_sizes = {
            "original_size": original_size,
            "original_size_human": original_size_human,
            "converted_size": converted_size,
            "converted_size_human": converted_size_human,
            "compression_ratio": compression_ratio
        }
    return file_sizes


def _resolve_parameters(config, doc_type, recursive, lossless_fallback, bnf_compliant, 
                       compression_ratio_tolerance, include_bnf_markers):
    """Resolve parameters using config defaults.
    
    Args:
        config: WorkflowConfig object
        doc_type: Document type (or None for default)
        recursive: Recursive flag (or None for default)
        lossless_fallback: Lossless fallback flag (or None for default)
        bnf_compliant: BnF compliant flag (or None for default)
        compression_ratio_tolerance: Compression ratio tolerance (or None for default)
        include_bnf_markers: Include BnF markers flag (or None for default)
        
    Returns:
        Tuple of resolved parameters
    """
    return (
        doc_type or config.document_type,
        config.recursive if recursive is None else recursive,
        config.lossless_fallback if lossless_fallback is None else lossless_fallback,
        config.bnf_compliant if bnf_compliant is None else bnf_compliant,
        config.compression_ratio_tolerance if compression_ratio_tolerance is None else compression_ratio_tolerance,
        config.include_bnf_markers if include_bnf_markers is None else include_bnf_markers
    )