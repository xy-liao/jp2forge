"""
Validation utilities for JP2Forge.

This module provides validation utilities for JPEG2000 files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

from utils.tools.jpylyzer_tool import JPylyzerTool
from utils.tools.tool_manager import ToolManager

logger = logging.getLogger(__name__)


class JP2Validator:
    """
    Validator for JPEG2000 files.

    This class provides methods for validating JPEG2000 files using
    various tools such as JPylyzer.
    """

    def __init__(
        self,
        tool_manager: Optional[ToolManager] = None,
        jpylyzer_path: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize the JP2 validator.

        Args:
            tool_manager: Optional tool manager to use for tool detection
            jpylyzer_path: Optional path to jpylyzer executable
            timeout: Timeout for command execution in seconds
        """
        self.tool_manager = tool_manager
        self.jpylyzer_path = jpylyzer_path
        self.timeout = timeout

        # Initialize JPylyzer
        self._init_jpylyzer()

        logger.info("JP2Validator initialized")

    def _init_jpylyzer(self) -> None:
        """
        Initialize JPylyzer tool.
        """
        # If tool manager is available, use it to get jpylyzer path
        if self.tool_manager is not None and self.jpylyzer_path is None:
            if self.tool_manager.is_available('jpylyzer'):
                self.jpylyzer_path = self.tool_manager.get_tool_path('jpylyzer')
                logger.info(f"Using jpylyzer from tool manager: {self.jpylyzer_path}")

        # Initialize JPylyzer tool
        self.jpylyzer = JPylyzerTool(
            jpylyzer_path=self.jpylyzer_path,
            timeout=self.timeout
        )

        if not self.jpylyzer.is_available():
            logger.warning(
                "JPylyzer not available. JPEG2000 validation will be limited."
            )

    def validate_jp2(
        self,
        file_path: Union[str, Path],
        format_type: str = "jp2"
    ) -> Dict[str, Any]:
        """
        Validate a JPEG2000 file.

        Args:
            file_path: Path to the JPEG2000 file
            format_type: JPEG2000 format type ('jp2', 'j2c', 'jph', 'jhc')

        Returns:
            Dict[str, Any]: Validation results
        """
        file_path_str = str(file_path)

        # Basic file checks
        if not os.path.exists(file_path_str):
            return {
                "isValid": False,
                "error": f"File not found: {file_path_str}"
            }

        # Check file extension
        ext = os.path.splitext(file_path_str)[1].lower()
        if format_type == "jp2" and ext != ".jp2":
            logger.warning(
                f"File extension '{ext}' doesn't match format type '{format_type}'"
            )

        # Use JPylyzer for validation if available
        if self.jpylyzer.is_available():
            # Set format type for JPylyzer
            self.jpylyzer.format_type = format_type

            # Validate with JPylyzer
            logger.info(f"Validating {file_path_str} with JPylyzer")
            validation_result = self.jpylyzer.validate(file_path_str)

            # Add metadata about validation
            validation_result["validationTool"] = "jpylyzer"
            validation_result["validationToolVersion"] = self.jpylyzer.get_version()

            return validation_result
        else:
            # Basic file validation without JPylyzer
            return self._basic_validation(file_path_str, format_type)

    def _basic_validation(
        self,
        file_path: str,
        format_type: str
    ) -> Dict[str, Any]:
        """
        Perform basic validation of a JPEG2000 file without external tools.

        Args:
            file_path: Path to the JPEG2000 file
            format_type: JPEG2000 format type

        Returns:
            Dict[str, Any]: Basic validation results
        """
        logger.warning(
            "Performing basic validation only (JPylyzer not available)"
        )

        result = {
            "isValid": False,
            "fileInfo": {
                "fileName": os.path.basename(file_path),
                "filePath": file_path,
                "fileSize": os.path.getsize(file_path)
            },
            "validationTool": "basic",
            "warnings": ["JPylyzer not available for full validation"],
            "tests": {},
            "properties": {}
        }

        try:
            # Check file signature
            with open(file_path, 'rb') as f:
                header = f.read(12)  # Read first 12 bytes

                # JP2 signature: 0x0000000C 'jP  '
                if format_type == "jp2" and header[0:12] == b'\x00\x00\x00\x0c\x6a\x50\x20\x20\x0d\x0a\x87\x0a':
                    result["isValid"] = True
                    result["tests"]["signatureTest"] = "passed"
                # J2C signature: 0xFF4FFF51
                elif format_type == "j2c" and header[0:4] == b'\xff\x4f\xff\x51':
                    result["isValid"] = True
                    result["tests"]["signatureTest"] = "passed"
                else:
                    result["isValid"] = False
                    result["tests"]["signatureTest"] = "failed"
                    result["warnings"].append(f"Invalid {format_type} signature")

            return result
        except Exception as e:
            logger.error(f"Error during basic validation: {e}")
            result["isValid"] = False
            result["error"] = str(e)
            return result

    def extract_properties(
        self,
        file_path: Union[str, Path],
        format_type: str = "jp2"
    ) -> Dict[str, Any]:
        """
        Extract properties from a JPEG2000 file.

        Args:
            file_path: Path to the JPEG2000 file
            format_type: JPEG2000 format type ('jp2', 'j2c', 'jph', 'jhc')

        Returns:
            Dict[str, Any]: Extracted properties
        """
        # This is similar to validate_jp2 since JPylyzer combines validation
        # and property extraction in a single operation
        return self.validate_jp2(file_path, format_type)

    def get_image_dimensions(
        self,
        jp2_properties: Dict[str, Any]
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract image dimensions from JPylyzer properties.

        Args:
            jp2_properties: Properties dictionary from JPylyzer

        Returns:
            Tuple[Optional[int], Optional[int]]: Width and height, or (None, None)
        """
        width = None
        height = None

        try:
            # Navigate the property tree
            props = jp2_properties.get("properties", {})

            # Try to find dimensions in JP2 header box
            if "jp2HeaderBox" in props:
                header_box = props["jp2HeaderBox"]
                if "imageHeaderBox" in header_box:
                    image_header = header_box["imageHeaderBox"]
                    width = int(image_header.get("width", 0))
                    height = int(image_header.get("height", 0))

            # If not found, try in the codestream
            if (width is None or height is None) and "contiguousCodestreamBox" in props:
                codestream = props["contiguousCodestreamBox"]
                if "siz" in codestream:
                    siz = codestream["siz"]
                    width = int(siz.get("xsiz", 0)) - int(siz.get("xosiz", 0))
                    height = int(siz.get("ysiz", 0)) - int(siz.get("yosiz", 0))

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Error extracting image dimensions: {e}")
            return None, None

        return width, height

    def is_valid_jp2(
        self,
        file_path: Union[str, Path],
        format_type: str = "jp2"
    ) -> bool:
        """
        Simple check if a JP2 file is valid.

        Args:
            file_path: Path to the JP2 file
            format_type: JPEG2000 format type

        Returns:
            bool: True if the file is valid
        """
        result = self.validate_jp2(file_path, format_type)
        return result.get("isValid", False)
