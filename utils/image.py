"""
Image processing utilities for JPEG2000 workflow.

This module provides utility functions for image processing
and validation.
"""

import os
import time
import logging
import numpy as np
from PIL import Image
from PIL.Image import DecompressionBombError
from functools import lru_cache
from typing import Tuple, Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Add is_multipage_tiff function to detect multi-page TIFFs
def is_multipage_tiff(input_file: str) -> Tuple[bool, int]:
    """
    Check if a TIFF file contains multiple pages and return the page count.
    
    Args:
        input_file: Path to input image file
        
    Returns:
        tuple: (is_multipage, page_count)
    """
    try:
        if not input_file.lower().endswith(('.tif', '.tiff')):
            return False, 1
            
        with Image.open(input_file) as img:
            # Check if the image has the n_frames attribute (multi-page)
            if hasattr(img, 'n_frames') and img.n_frames > 1:
                return True, img.n_frames
            return False, 1
    except Exception as e:
        logger.warning(f"Error checking multi-page status for {input_file}: {str(e)}")
        return False, 1

def extract_tiff_page(input_file: str, page_num: int, output_dir: str) -> str:
    """
    Extract a specific page from a multi-page TIFF file.
    
    Args:
        input_file: Path to input TIFF file
        page_num: Page number to extract (0-based)
        output_dir: Directory to save extracted page
        
    Returns:
        str: Path to extracted page file
    """
    try:
        # Create temporary directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        
        # Create temporary file for extracted page
        temp_file = os.path.join(output_dir, f"{base_name}_page_{page_num}.tif")
        
        with Image.open(input_file) as img:
            # Check if the requested page exists
            if not hasattr(img, 'n_frames') or page_num >= img.n_frames:
                raise ValueError(f"Page {page_num} does not exist in {input_file}")
                
            # Go to specified page
            img.seek(page_num)
            
            # Save as a single-page TIFF
            img.save(temp_file)
            
        logger.debug(f"Extracted page {page_num} from {input_file} to {temp_file}")
        return temp_file
    except Exception as e:
        logger.error(f"Error extracting page {page_num} from {input_file}: {str(e)}")
        raise


@lru_cache(maxsize=100)
def validate_image(input_file: str) -> Tuple[bool, str]:
    """
    Validate image file integrity with caching for repeated access.
    
    Args:
        input_file: Path to input image file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Check if file exists and is not empty
        if not os.path.exists(input_file):
            return False, "File does not exist"
        if os.path.getsize(input_file) == 0:
            return False, "File is empty"
        
        # Check if file is a valid image using PIL
        try:
            with Image.open(input_file) as img:
                img.verify()
                # Check for reasonable dimensions
                width, height = img.size
                if width <= 0 or height <= 0:
                    return False, "Invalid image dimensions"
                if width * height > 178956970:  # Max reasonable size ~180MP
                    return False, "Image dimensions exceed maximum allowed"
                
                # Check if format is supported
                if img.format.lower() not in ['tiff', 'jpeg', 'png']:
                    return False, f"Invalid image format: {img.format}"
            
            return True, ""
            
        except (IOError, SyntaxError) as e:
            return False, f"Invalid image file: {str(e)}"
        
    except DecompressionBombError:
        return False, "Image is too large to process safely"
    except OSError as e:
        return False, f"File is corrupted: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error validating image: {str(e)}"


def get_output_path(input_file: str, output_dir: str, extension: str) -> str:
    """
    Generate output path for converted file with collision handling.
    
    Args:
        input_file: Path to input file
        output_dir: Directory for output files
        extension: Output file extension
        
    Returns:
        str: Path to output file
        
    Raises:
        FileNotFoundError: If the output directory doesn't exist and can't be created
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        except OSError as e:
            logger.error(f"Failed to create output directory {output_dir}: {str(e)}")
            raise FileNotFoundError(f"Output directory {output_dir} does not exist and could not be created") from e
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output filename with new extension
    output_filename = f"{base_name}{extension}"
    output_path = os.path.join(output_dir, output_filename)
    
    # Handle filename collisions
    counter = 1
    while os.path.exists(output_path):
        # If file already exists, add a counter to the filename
        output_filename = f"{base_name}_{counter}{extension}"
        output_path = os.path.join(output_dir, output_filename)
        counter += 1
        
        # Prevent infinite loop if somehow we can't find a unique name
        if counter > 1000:
            timestamp = int(time.time())
            output_filename = f"{base_name}_{timestamp}{extension}"
            output_path = os.path.join(output_dir, output_filename)
            logger.warning(f"Had to use timestamp to create unique filename: {output_filename}")
            break
    
    return output_path

# Add a function to generate multi-page output paths
def get_multipage_output_paths(input_file: str, output_dir: str, extension: str, page_count: int) -> List[str]:
    """
    Generate output paths for multiple pages of a multi-page TIFF.
    
    Args:
        input_file: Path to input file
        output_dir: Directory for output files
        extension: Output file extension
        page_count: Number of pages
        
    Returns:
        list: List of output paths for each page
    """
    output_paths = []
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    for page_num in range(page_count):
        # Create output filename with page number
        output_filename = f"{base_name}_page_{page_num}{extension}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Handle filename collisions
        counter = 1
        while os.path.exists(output_path) and output_path not in output_paths:
            output_filename = f"{base_name}_page_{page_num}_{counter}{extension}"
            output_path = os.path.join(output_dir, output_filename)
            counter += 1
            
            # Prevent infinite loop
            if counter > 1000:
                timestamp = int(time.time())
                output_filename = f"{base_name}_page_{page_num}_{timestamp}{extension}"
                output_path = os.path.join(output_dir, output_filename)
                logger.warning(f"Had to use timestamp to create unique filename: {output_filename}")
                break
        
        output_paths.append(output_path)
    
    return output_paths

def should_process_in_chunks(input_file: str, memory_limit_mb: int) -> Tuple[bool, Optional[int]]:
    """
    Determine if an image should be processed in chunks based on size and estimate chunk size.
    
    Args:
        input_file: Path to input image
        memory_limit_mb: Memory limit in MB
        
    Returns:
        tuple: (should_chunk, suggested_chunk_size)
    """
    try:
        with Image.open(input_file) as img:
            width, height = img.size
            num_bands = len(img.getbands())
            
            # Calculate image size in memory
            # Each pixel takes num_bands * bytes_per_band (usually 1 for 8-bit depth)
            # Add 50% overhead for processing
            bytes_per_band = 1
            if img.mode in ["I", "F"]:
                bytes_per_band = 4  # 32-bit integer or float
            elif img.mode in ["I;16", "I;16L", "I;16B"]:
                bytes_per_band = 2  # 16-bit
                
            # Estimate memory usage in MB: width * height * bands * bytes_per_band + 50% overhead
            estimated_mb = (width * height * num_bands * bytes_per_band * 1.5) / (1024 * 1024)
            
            logger.debug(f"Image size: {width}x{height}, estimated memory: {estimated_mb:.2f} MB")
            
            # Determine if we need chunking
            should_chunk = estimated_mb > memory_limit_mb / 4
            
            # Calculate suggested chunk size if needed
            chunk_size = None
            if should_chunk:
                # Find a chunk_height that keeps memory usage reasonable
                # We chunk by rows for simplicity
                target_chunk_mb = memory_limit_mb / 8  # Use 1/8 of memory limit per chunk
                bytes_per_row = width * num_bands * bytes_per_band * 1.5
                rows_per_chunk = int((target_chunk_mb * 1024 * 1024) / bytes_per_row)
                
                # Ensure at least 10 rows and at most 1/4 of the image
                rows_per_chunk = max(10, min(rows_per_chunk, height // 4))
                chunk_size = rows_per_chunk
                
                logger.debug(f"Will process in chunks of {rows_per_chunk} rows")
            
            return should_chunk, chunk_size
    except Exception as e:
        logger.warning(f"Error determining chunk size for {input_file}: {str(e)}")
        # If we can't determine, err on the side of caution and use default chunk size
        return True, None


def calculate_mse(orig_array: np.ndarray, conv_array: np.ndarray) -> float:
    """
    Calculate Mean Square Error between images.
    
    Args:
        orig_array: Original image as NumPy array
        conv_array: Converted image as NumPy array
        
    Returns:
        float: Mean Square Error
    """
    return np.mean((orig_array - conv_array) ** 2)


def calculate_psnr(mse: float) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio.
    
    Args:
        mse: Mean Square Error
        
    Returns:
        float: Peak Signal-to-Noise Ratio in dB
    """
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    return 20 * np.log10(max_pixel / np.sqrt(mse))


def calculate_ssim(orig_array: np.ndarray, conv_array: np.ndarray) -> float:
    """
    Calculate Structural Similarity Index.
    
    Args:
        orig_array: Original image as NumPy array
        conv_array: Converted image as NumPy array
        
    Returns:
        float: Structural Similarity Index
    """
    # Simplified SSIM calculation
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    
    mean_x = np.mean(orig_array)
    mean_y = np.mean(conv_array)
    std_x = np.std(orig_array)
    std_y = np.std(conv_array)
    cov = np.mean((orig_array - mean_x) * (conv_array - mean_y))
    
    numerator = (2 * mean_x * mean_y + c1) * (2 * cov + c2)
    denominator = (
        (mean_x ** 2 + mean_y ** 2 + c1) *
        (std_x ** 2 + std_y ** 2 + c2)
    )
    
    return numerator / denominator


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        float: Memory usage in MB
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # If psutil is not available, return a default value
        return 0.0


def find_image_files(directory: str, recursive: bool = False) -> list:
    """
    Find image files in a directory.
    
    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories
        
    Returns:
        list: List of image file paths
    """
    image_files = []
    for root, _, files in os.walk(directory):
        if not recursive and root != directory:
            continue
            
        for file in files:
            if file.lower().endswith(('.tif', '.tiff', '.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(root, file))
    
    return image_files
