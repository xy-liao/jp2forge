"""
External tool management utilities for JP2Forge.

This package provides tools for detecting, managing, and interfacing
with external dependencies like Kakadu and ExifTool.
"""

from utils.tools.tool_manager import ToolManager
from utils.tools.kakadu_tool import KakaduTool
from utils.tools.exiftool import ExifTool

__all__ = ['ToolManager', 'KakaduTool', 'ExifTool']
