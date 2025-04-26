"""
File I/O utilities for JPEG2000 workflow.

This module provides utility functions for file operations in
the JPEG2000 workflow.
"""

import os
import logging
import json
import shutil
from typing import Dict, Any, List, Union, Optional

logger = logging.getLogger(__name__)


def ensure_directory(directory: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to directory

    Returns:
        bool: True if successful
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False


def get_file_size(file_path: str) -> int:
    """
    Get size of a file in bytes.

    Args:
        file_path: Path to file

    Returns:
        int: File size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return 0


def get_file_extension(file_path: str) -> str:
    """
    Get the extension of a file.

    Args:
        file_path: Path to file

    Returns:
        str: File extension
    """
    return os.path.splitext(file_path)[1].lower()


def is_image_file(file_path: str) -> bool:
    """
    Check if a file is an image file based on extension.

    Args:
        file_path: Path to file

    Returns:
        bool: True if file is an image
    """
    return get_file_extension(file_path) in ['.tif', '.tiff', '.jpg', '.jpeg', '.png', '.jp2', '.j2k']


def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Load JSON data from a file.

    Args:
        file_path: Path to JSON file

    Returns:
        dict: Loaded JSON data, or None if loading fails
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {str(e)}")
        return None


def save_json(data: Dict[str, Any], file_path: str, indent: int = 4) -> bool:
    """
    Save JSON data to a file.

    Args:
        data: Data to save
        file_path: Path to output file
        indent: Indentation level for JSON

    Returns:
        bool: True if successful
    """
    try:
        ensure_directory(os.path.dirname(file_path))
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {str(e)}")
        return False


def copy_file(source: str, destination: str, overwrite: bool = False) -> bool:
    """
    Copy a file from source to destination.

    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite existing files

    Returns:
        bool: True if successful
    """
    try:
        if os.path.exists(destination) and not overwrite:
            logger.warning(f"File {destination} already exists")
            return False

        ensure_directory(os.path.dirname(destination))
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"Error copying file {source} to {destination}: {str(e)}")
        return False


def delete_file(file_path: str) -> bool:
    """
    Delete a file.

    Args:
        file_path: Path to file to delete

    Returns:
        bool: True if successful
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        else:
            logger.warning(f"File {file_path} does not exist")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False
