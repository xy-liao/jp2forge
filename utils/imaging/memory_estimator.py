"""
Memory usage estimation for image processing.

This module provides functions to estimate memory requirements
for image processing operations.
"""

import logging
import psutil
from typing import Tuple, Optional, Dict, Any
from PIL import Image

logger = logging.getLogger(__name__)

# Memory multipliers for different operations
MEMORY_MULTIPLIERS = {
    'load': 1.0,  # Base memory for loading image
    'process': 2.0,  # Processing typically needs original + new copy
    'compress': 3.0,  # Compression may need multiple copies
    'analyze': 2.5,  # Analysis may need multiple intermediate representations
}

# Memory usage per pixel for different modes (in bytes)
BYTES_PER_PIXEL = {
    '1': 1 / 8,    # 1-bit pixels
    'L': 1,      # 8-bit pixels, grayscale
    'P': 1,      # 8-bit pixels, mapped to palette
    'RGB': 3,    # 3x8-bit pixels, true color
    'RGBA': 4,   # 4x8-bit pixels, true color with transparency
    'CMYK': 4,   # 4x8-bit pixels, color separation
    'YCbCr': 3,  # 3x8-bit pixels, color video format
    'LAB': 3,    # 3x8-bit pixels, L*a*b color space
    'HSV': 3,    # 3x8-bit pixels, Hue, Saturation, Value color space
    'I': 4,      # 32-bit signed integer pixels
    'F': 4,      # 32-bit floating point pixels
    'I;16': 2,   # 16-bit unsigned integer pixels
    'I;16B': 2,  # 16-bit big-endian unsigned integer pixels
    'I;16L': 2,  # 16-bit little-endian unsigned integer pixels
    'I;16S': 2,  # 16-bit signed integer pixels
    'I;16BS': 2,  # 16-bit big-endian signed integer pixels
    'I;16LS': 2,  # 16-bit little-endian signed integer pixels
    'I;32': 4,   # 32-bit unsigned integer pixels
    'I;32B': 4,  # 32-bit big-endian unsigned integer pixels
    'I;32L': 4,  # 32-bit little-endian unsigned integer pixels
    'I;32S': 4,  # 32-bit signed integer pixels
    'I;32BS': 4,  # 32-bit big-endian signed integer pixels
    'I;32LS': 4,  # 32-bit little-endian signed integer pixels
}


def estimate_memory_usage(
    width: int,
    height: int,
    mode: str,
    operation: str = 'process'
) -> int:
    """
    Estimate memory usage for an image operation.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        mode: Image mode (e.g., 'RGB', 'L')
        operation: Operation type ('load', 'process', 'compress', 'analyze')

    Returns:
        int: Estimated memory usage in bytes
    """
    # Get bytes per pixel for the mode
    bytes_per_pixel = BYTES_PER_PIXEL.get(mode, 4)  # Default to 4 bytes if unknown

    # Get memory multiplier for the operation
    multiplier = MEMORY_MULTIPLIERS.get(operation, 2.0)  # Default to 2.0 if unknown

    # Calculate base memory usage
    pixel_count = width * height
    base_memory = pixel_count * bytes_per_pixel

    # Apply multiplier for the operation
    total_memory = int(base_memory * multiplier)

    logger.debug(
        f"Memory estimate for {width}x{height} {mode} image, operation '{operation}': "
        f"{total_memory / (1024 * 1024):.2f} MB"
    )

    return total_memory


def calculate_optimal_chunk_size(
    width: int,
    height: int,
    mode: str,
    operation: str = 'process',
    memory_limit_mb: Optional[int] = None,
    min_chunk_height: int = 16
) -> int:
    """
    Calculate optimal chunk height for processing a large image.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        mode: Image mode (e.g., 'RGB', 'L')
        operation: Operation type ('load', 'process', 'compress', 'analyze')
        memory_limit_mb: Memory limit in MB, or None to use 50% of system memory
        min_chunk_height: Minimum chunk height in pixels

    Returns:
        int: Optimal chunk height in pixels
    """
    # Determine memory limit if not specified
    if memory_limit_mb is None:
        system_memory = psutil.virtual_memory().total
        memory_limit = int(system_memory * 0.5)  # Use 50% of system memory
    else:
        memory_limit = memory_limit_mb * 1024 * 1024  # Convert MB to bytes

    # Calculate memory per row
    bytes_per_pixel = BYTES_PER_PIXEL.get(mode, 4)
    memory_per_row = width * bytes_per_pixel * MEMORY_MULTIPLIERS.get(operation, 2.0)

    # Calculate maximum rows based on memory limit
    max_rows = max(min_chunk_height, int(memory_limit / memory_per_row))

    # Ensure we don't exceed image height
    chunk_height = min(max_rows, height)

    logger.debug(
        f"Optimal chunk height for {width}x{height} {mode} image: "
        f"{chunk_height} rows ({chunk_height/height*100:.1f}% of image)"
    )

    return chunk_height


def get_image_dimensions_and_mode(image_path: str) -> Tuple[int, int, str]:
    """
    Get image dimensions and mode without loading the entire image.

    Args:
        image_path: Path to the image file

    Returns:
        tuple: (width, height, mode)
    """
    try:
        with Image.open(image_path) as img:
            return img.width, img.height, img.mode
    except Exception as e:
        logger.error(f"Error reading image dimensions: {e}")
        raise


def estimate_image_file_memory(
    image_path: str,
    operation: str = 'process'
) -> Dict[str, Any]:
    """
    Estimate memory requirements for an image file.

    Args:
        image_path: Path to the image file
        operation: Operation type ('load', 'process', 'compress', 'analyze')

    Returns:
        dict: Memory estimation details
    """
    # Get image dimensions and mode
    width, height, mode = get_image_dimensions_and_mode(image_path)

    # Estimate memory usage
    memory_bytes = estimate_memory_usage(width, height, mode, operation)

    # Get system memory for comparison
    system_memory = psutil.virtual_memory().total

    # Calculate percentage of system memory
    memory_percentage = (memory_bytes / system_memory) * 100

    result = {
        'width': width,
        'height': height,
        'mode': mode,
        'pixel_count': width * height,
        'memory_bytes': memory_bytes,
        'memory_mb': memory_bytes / (1024 * 1024),
        'memory_percentage': memory_percentage,
        'exceeds_half_ram': memory_bytes > (system_memory / 2),
        'exceeds_ram': memory_bytes > system_memory,
        'recommended_chunking': memory_bytes > (system_memory / 4)
    }

    logger.debug(
        f"Memory estimation for {image_path}: "
        f"{result['memory_mb']:.2f} MB ({result['memory_percentage']:.1f}% of system RAM)"
    )

    return result
