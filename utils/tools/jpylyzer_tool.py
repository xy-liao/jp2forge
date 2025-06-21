"""
JPylyzer interface for JP2Forge.

This module provides a wrapper for JPylyzer to validate and extract
properties from JP2 files.
"""

import os
import logging
import subprocess
from typing import Dict, Any, Optional, List, Union, Tuple

try:
    from defusedxml import ElementTree as ET
    from defusedxml.ElementTree import fromstring as ET_fromstring
    USING_DEFUSED_XML = True
    import xml.etree.ElementTree as _ET  # for type hints only
except ImportError:
    import xml.etree.ElementTree as ET
    from xml.etree.ElementTree import fromstring as ET_fromstring
    import warnings
    warnings.warn("defusedxml not available, falling back to xml.etree.ElementTree. Consider installing defusedxml for security.", ImportWarning)
    USING_DEFUSED_XML = False
    import xml.etree.ElementTree as _ET  # for type hints only

from ..security import validate_tool_path, validate_file_path, validate_subprocess_args

logger = logging.getLogger(__name__)


class JPylyzerTool:
    """
    Interface for JPylyzer operations.

    This class provides methods for validating and extracting properties
    from JP2 files using JPylyzer.
    """

    def __init__(
        self,
        jpylyzer_path: Optional[str] = None,
        timeout: int = 60,
        format_type: str = "jp2"
    ):
        """
        Initialize the JPylyzer interface.

        Args:
            jpylyzer_path: Path to jpylyzer executable or None for default
            timeout: Timeout for command execution in seconds
            format_type: JPEG2000 format type ('jp2', 'j2c', 'jph', 'jhc')
        """
        self.jpylyzer_path = jpylyzer_path
        self.timeout = timeout
        self.format_type = format_type

        # If no path provided, try to find jpylyzer on PATH
        if self.jpylyzer_path is None:
            import shutil
            self.jpylyzer_path = shutil.which('jpylyzer')

        # Validate JPylyzer path using security validation
        if self.jpylyzer_path and not validate_tool_path(self.jpylyzer_path, "jpylyzer"):
            logger.warning(f"JPylyzer validation failed: {self.jpylyzer_path}")
            self.jpylyzer_path = None

        # Try to use JPylyzer as a module if executable not found
        self.use_module = False
        if self.jpylyzer_path is None:
            try:
                import jpylyzer
                self.use_module = True
                logger.info("Using JPylyzer as a Python module")
            except ImportError:
                logger.warning("JPylyzer not found as executable or module")
        else:
            logger.info(f"Initialized JPylyzer interface with executable at {self.jpylyzer_path}")

    def is_available(self) -> bool:
        """
        Check if JPylyzer is available.

        Returns:
            bool: True if JPylyzer is available, False otherwise
        """
        if self.use_module:
            return True

        if self.jpylyzer_path is None:
            return False

        try:
            result = subprocess.run(
                [self.jpylyzer_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Error checking JPylyzer availability: {e}")
            return False

    def get_version(self) -> Optional[str]:
        """
        Get the version of JPylyzer.

        Returns:
            Optional[str]: JPylyzer version or None if not available
        """
        if self.use_module:
            try:
                import jpylyzer
                return getattr(jpylyzer, '__version__', 'Unknown')
            except ImportError:
                return None

        if not self.is_available():
            return None

        try:
            result = subprocess.run(
                [self.jpylyzer_path, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode == 0:
                # Extract version number from output
                version_line = result.stdout.strip()
                return version_line
            return None
        except Exception as e:
            logger.warning(f"Error getting JPylyzer version: {e}")
            return None

    def validate(self, jp2_file: str) -> Dict[str, Any]:
        """
        Validate a JPEG2000 file using JPylyzer.

        Args:
            jp2_file: Path to the JPEG2000 file to validate

        Returns:
            Dict[str, Any]: Validation results including validity and properties
        """
        # Validate file path
        if not validate_file_path(jp2_file):
            return {"error": f"File validation failed: {jp2_file}"}

        if self.use_module:
            return self._validate_with_module(jp2_file)

        if not self.is_available():
            return {"error": "JPylyzer is not available"}

        try:
            cmd = [self.jpylyzer_path]

            # Add format option if needed
            if self.format_type != "jp2":
                cmd.extend(["--format", self.format_type])

            # Add file to analyze
            cmd.append(jp2_file)
            
            # Validate command arguments
            if not validate_subprocess_args(cmd):
                return {"error": "Invalid command arguments detected"}

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode != 0:
                logger.error(
                    f"JPylyzer failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return {"error": result.stderr.strip()}

            # Parse the XML output
            return self._parse_jpylyzer_output(result.stdout)

        except Exception as e:
            logger.error(f"Error validating JPEG2000 file with JPylyzer: {e}")
            return {"error": str(e)}

    def _validate_with_module(self, jp2_file: str) -> Dict[str, Any]:
        """
        Validate a JPEG2000 file using JPylyzer as a Python module.

        Args:
            jp2_file: Path to the JPEG2000 file to validate

        Returns:
            Dict[str, Any]: Validation results
        """
        try:
            from jpylyzer import jpylyzer

            # Call JPylyzer's checkOneFile function
            result_elem = jpylyzer.checkOneFile(jp2_file, self.format_type)

            # Convert the ElementTree element to a string
            xml_str = ET.tostring(result_elem, encoding='utf-8').decode('utf-8')

            # Parse the XML output
            return self._parse_jpylyzer_output(xml_str)

        except ImportError:
            return {"error": "JPylyzer module not available"}
        except Exception as e:
            logger.error(f"Error validating with JPylyzer module: {e}")
            return {"error": str(e)}

    def extract_properties(self, jp2_file: str) -> Dict[str, Any]:
        """
        Extract properties from a JPEG2000 file using JPylyzer.
        This is an alias for validate() since JPylyzer combines validation
        and property extraction.

        Args:
            jp2_file: Path to the JPEG2000 file

        Returns:
            Dict[str, Any]: Extracted properties
        """
        return self.validate(jp2_file)

    def _strip_namespace(self, obj):
        """
        Recursively remove XML namespaces from dictionary keys.
        """
        if isinstance(obj, dict):
            new_obj = {}
            for k, v in obj.items():
                # Remove namespace if present
                if '}' in k:
                    k_clean = k.split('}', 1)[1]
                else:
                    k_clean = k
                new_obj[k_clean] = self._strip_namespace(v)
            return new_obj
        elif isinstance(obj, list):
            return [self._strip_namespace(i) for i in obj]
        else:
            return obj

    def _parse_jpylyzer_output(self, xml_output: str) -> Dict[str, Any]:
        """
        Parse the XML output from JPylyzer and convert it to a dictionary.
        Handles XML namespaces and <isValid> attributes.
        """
        try:
            # Parse XML and handle namespaces
            ns = {'jpy': 'http://openpreservation.org/ns/jpylyzer/v2/'}
            root = ET_fromstring(xml_output)  # nosec B314 - using defusedxml when available
            result = {
                "toolInfo": {},
                "fileInfo": {},
                "isValid": False,
                "tests": {},
                "properties": {},
                "warnings": []
            }

            # Find isValid element (with or without namespace/attribute)
            is_valid_elem = root.find('.//jpy:isValid', ns)
            if is_valid_elem is not None:
                result["isValid"] = is_valid_elem.text.strip().lower() == "true"
            else:
                # fallback: try without namespace
                is_valid_elem = root.find('.//isValid')
                if is_valid_elem is not None:
                    result["isValid"] = is_valid_elem.text.strip().lower() == "true"

            # Get tool info
            tool_info = root.find(".//jpy:toolInfo", ns) or root.find(".//toolInfo")
            if tool_info is not None:
                for child in tool_info:
                    result["toolInfo"][child.tag.split('}', 1)[-1]] = child.text

            # Get file info
            file_elem = root.find(".//jpy:file", ns) or root.find(".//file")
            if file_elem is not None:
                file_info = file_elem.find(".//jpy:fileInfo", ns) or file_elem.find(".//fileInfo")
                if file_info is not None:
                    for child in file_info:
                        result["fileInfo"][child.tag.split('}', 1)[-1]] = child.text
                # Get warnings
                warnings_elems = file_elem.findall(
                    ".//jpy:warnings/jpy:warning", ns) or file_elem.findall(".//warnings/warning")
                if warnings_elems:
                    for warning in warnings_elems:
                        if warning.text:
                            result["warnings"].append(warning.text)
                # Get properties
                props_elem = file_elem.find(
                    ".//jpy:properties", ns) or file_elem.find(".//properties")
                if props_elem is not None:
                    self._parse_recursive(props_elem, result["properties"])
                # Get tests
                tests_elem = file_elem.find(".//jpy:tests", ns) or file_elem.find(".//tests")
                if tests_elem is not None:
                    self._parse_recursive(tests_elem, result["tests"])
            # Strip namespaces from all keys before returning
            return self._strip_namespace(result)
        except Exception as e:
            logger.error(f"Error parsing JPylyzer output: {e}")
            return {"error": f"Failed to parse JPylyzer output: {str(e)}"}

    def _parse_recursive(self, elem: _ET.Element, target_dict: Dict[str, Any]) -> None:
        """
        Recursively parse XML elements into a dictionary.
        
        Args:
            elem: Current XML element
            target_dict: Target dictionary to populate
        """
        for child in elem:
            # Skip the element itself
            if child.tag == elem.tag:
                continue

            # If it has children, create a new dict and parse recursively
            if len(child) > 0:
                new_dict = {}
                self._parse_recursive(child, new_dict)
                target_dict[child.tag] = new_dict
            # Otherwise just add the text value
            elif child.text:
                target_dict[child.tag] = child.text
