"""
Security utilities for JP2Forge.

This module provides security-related utilities including input validation
and sanitization for subprocess calls.
"""

import os
import re
import shlex
from typing import List, Optional, Union
from pathlib import Path


def validate_file_path(file_path: Union[str, Path]) -> bool:
    """
    Validate that a file path is safe and exists.
    
    Args:
        file_path: Path to validate
        
    Returns:
        bool: True if path is valid and safe, False otherwise
    """
    if not file_path:
        return False
        
    try:
        path = Path(file_path).resolve()
        
        # Check if path exists
        if not path.exists():
            return False
            
        # Check for path traversal attempts
        if ".." in str(path):
            return False
            
        # Check if it's actually a file (not a directory or special file)
        if not path.is_file():
            return False
            
        return True
    except (OSError, ValueError):
        return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return ""
        
    # Remove or replace dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        sanitized = "file"
        
    return sanitized


def validate_subprocess_args(args: List[str]) -> bool:
    """
    Validate subprocess arguments for basic safety.
    
    Args:
        args: List of command arguments
        
    Returns:
        bool: True if arguments appear safe, False otherwise
    """
    if not args or not isinstance(args, list):
        return False
        
    # Check for shell injection patterns
    dangerous_patterns = [
        ';', '&&', '||', '|', '>', '<', '`', '$', 
        '$(', '${', '\n', '\r'
    ]
    
    for arg in args:
        if not isinstance(arg, str):
            return False
            
        # Check for dangerous shell characters
        for pattern in dangerous_patterns:
            if pattern in arg:
                return False
                
    return True


def sanitize_subprocess_args(args: List[str]) -> List[str]:
    """
    Sanitize subprocess arguments by shell-escaping them.
    
    Args:
        args: List of command arguments
        
    Returns:
        List[str]: Sanitized arguments
    """
    if not args:
        return []
        
    sanitized = []
    for arg in args:
        if isinstance(arg, str):
            # Use shlex.quote to safely escape the argument
            sanitized.append(shlex.quote(arg))
        else:
            # Convert to string and escape
            sanitized.append(shlex.quote(str(arg)))
            
    return sanitized


def validate_tool_path(tool_path: str, expected_name: Optional[str] = None) -> bool:
    """
    Validate that a tool path is safe to execute.
    
    Args:
        tool_path: Path to the tool executable
        expected_name: Expected name of the tool (optional)
        
    Returns:
        bool: True if tool path is valid, False otherwise
    """
    if not tool_path:
        return False
        
    try:
        path = Path(tool_path).resolve()
        
        # Check if path exists and is executable
        if not path.exists() or not os.access(path, os.X_OK):
            return False
            
        # Check if it's actually a file
        if not path.is_file():
            return False
            
        # If expected name is provided, validate it
        if expected_name:
            if expected_name.lower() not in path.name.lower():
                return False
                
        return True
    except (OSError, ValueError):
        return False