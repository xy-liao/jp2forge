"""
External tool manager for JP2Forge.

This module provides tools for detecting, managing, and interfacing
with external dependencies required by JP2Forge.
"""

import os
import sys
import logging
import subprocess
import shutil
from typing import Dict, Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)


class ToolManager:
    """
    Manager for external tool dependencies.

    This class handles detection and management of external tools
    required by JP2Forge, such as Kakadu and ExifTool.
    """

    def __init__(
        self,
        prefer_system_tools: bool = True,
        tool_paths: Optional[Dict[str, str]] = None,
        timeout: int = 60
    ):
        """
        Initialize the tool manager.

        Args:
            prefer_system_tools: Whether to prefer system tools over bundled ones
            tool_paths: Optional dictionary of tool paths
            timeout: Timeout for tool execution in seconds
        """
        self.prefer_system_tools = prefer_system_tools
        self.tool_paths = tool_paths or {}
        self.timeout = timeout

        # Initialize tool availability
        self._available_tools = {}
        self._tool_versions = {}

        # Detect available tools
        self.detect_tools()

        logger.debug(
            f"ToolManager initialized with {len(self._available_tools)} "
            f"available tools"
        )

    def detect_tools(self) -> None:
        """
        Detect available external tools.
        """
        # Reset tool availability
        self._available_tools = {}
        self._tool_versions = {}

        # Detect common tools
        self._detect_exiftool()
        self._detect_kakadu()
        self._detect_jpylyzer()

        logger.info(
            f"Detected {len(self._available_tools)} available tools: "
            f"{', '.join(self._available_tools.keys())}"
        )

    def _detect_exiftool(self) -> None:
        """
        Detect ExifTool availability.
        """
        # Check custom path first
        exiftool_path = self.tool_paths.get('exiftool')

        if exiftool_path and os.path.exists(exiftool_path):
            # Verify it works
            if self._verify_exiftool(exiftool_path):
                self._available_tools['exiftool'] = exiftool_path
                return

        # If prefer system tools, check in PATH first
        if self.prefer_system_tools:
            exiftool_path = shutil.which('exiftool')
            if exiftool_path:
                if self._verify_exiftool(exiftool_path):
                    self._available_tools['exiftool'] = exiftool_path
                    return

        # Check common installation locations
        common_paths = [
            '/usr/bin/exiftool',
            '/usr/local/bin/exiftool',
            '/opt/homebrew/bin/exiftool',
            'C:\\Program Files\\ExifTool\\exiftool.exe',
            'C:\\Program Files (x86)\\ExifTool\\exiftool.exe'
        ]

        for path in common_paths:
            if os.path.exists(path):
                if self._verify_exiftool(path):
                    self._available_tools['exiftool'] = path
                    return

        logger.warning("ExifTool not found, metadata operations may fail")

    def _verify_exiftool(self, path: str) -> bool:
        """
        Verify that the ExifTool at the given path works.

        Args:
            path: Path to ExifTool

        Returns:
            bool: True if ExifTool works
        """
        try:
            result = subprocess.run(
                [path, '-ver'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Found ExifTool {version} at {path}")
                self._tool_versions['exiftool'] = version
                return True
            else:
                logger.warning(
                    f"ExifTool at {path} failed verification: "
                    f"{result.stderr.strip()}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error verifying ExifTool at {path}: {e}")
            return False

    def _detect_kakadu(self) -> None:
        """
        Detect Kakadu availability.
        """
        # Check custom path first
        kakadu_path = self.tool_paths.get('kakadu')

        if kakadu_path and os.path.isdir(kakadu_path):
            # Look for kdu_compress in the directory
            kdu_compress = os.path.join(kakadu_path, 'kdu_compress')
            if sys.platform == 'win32':
                kdu_compress += '.exe'

            if os.path.exists(kdu_compress):
                if self._verify_kakadu(kdu_compress):
                    self._available_tools['kakadu'] = kdu_compress
                    return

        # If prefer system tools, check in PATH first
        if self.prefer_system_tools:
            kdu_compress = shutil.which('kdu_compress')
            if kdu_compress:
                if self._verify_kakadu(kdu_compress):
                    self._available_tools['kakadu'] = kdu_compress
                    return

        # Check common installation locations
        common_paths = [
            '/usr/bin/kdu_compress',
            '/usr/local/bin/kdu_compress',
            '/opt/homebrew/bin/kdu_compress',
            '/opt/kakadu/kdu_compress',
            'C:\\Program Files\\Kakadu\\kdu_compress.exe',
            'C:\\Kakadu\\kdu_compress.exe'
        ]

        for path in common_paths:
            if os.path.exists(path):
                if self._verify_kakadu(path):
                    self._available_tools['kakadu'] = path
                    return

        logger.info("Kakadu not found, will use Pillow for JPEG2000 operations")

    def _verify_kakadu(self, path: str) -> bool:
        """
        Verify that the Kakadu installation at the given path works.

        Args:
            path: Path to kdu_compress

        Returns:
            bool: True if Kakadu works
        """
        try:
            result = subprocess.run(
                [path, '-v'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            # Kakadu outputs version to stderr
            output = result.stderr.strip() or result.stdout.strip()

            if 'Kakadu' in output:
                # Extract version if possible
                for line in output.split('\n'):
                    if 'Version' in line:
                        version = line.strip()
                        self._tool_versions['kakadu'] = version
                        logger.info(f"Found Kakadu ({version}) at {path}")
                        return True

                # If version not found, just log generic info
                logger.info(f"Found Kakadu at {path}")
                self._tool_versions['kakadu'] = 'Unknown version'
                return True
            else:
                logger.warning(
                    f"Kakadu at {path} failed verification: "
                    f"Output does not contain 'Kakadu'"
                )
                return False

        except Exception as e:
            logger.warning(f"Error verifying Kakadu at {path}: {e}")
            return False

    def _detect_jpylyzer(self) -> None:
        """
        Detect jpylyzer availability.
        """
        # If prefer system tools, check in PATH first
        if self.prefer_system_tools:
            jpylyzer_path = shutil.which('jpylyzer')
            if jpylyzer_path:
                if self._verify_jpylyzer(jpylyzer_path):
                    self._available_tools['jpylyzer'] = jpylyzer_path
                    return

        # Check Python modules
        try:
            import jpylyzer
            self._available_tools['jpylyzer_module'] = 'jpylyzer'
            self._tool_versions['jpylyzer'] = getattr(jpylyzer, '__version__', 'Unknown')
            logger.info(f"Found jpylyzer module version {self._tool_versions['jpylyzer']}")
            return
        except ImportError:
            pass

        # Check common installation locations
        common_paths = [
            '/usr/bin/jpylyzer',
            '/usr/local/bin/jpylyzer',
            '/opt/homebrew/bin/jpylyzer',
            'C:\\Program Files\\jpylyzer\\jpylyzer.exe',
            'C:\\Program Files (x86)\\jpylyzer\\jpylyzer.exe'
        ]

        for path in common_paths:
            if os.path.exists(path):
                if self._verify_jpylyzer(path):
                    self._available_tools['jpylyzer'] = path
                    return

    def _verify_jpylyzer(self, path: str) -> bool:
        """
        Verify that jpylyzer at the given path works.

        Args:
            path: Path to jpylyzer

        Returns:
            bool: True if jpylyzer works
        """
        try:
            result = subprocess.run(
                [path, '--version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"Found jpylyzer {version} at {path}")
                self._tool_versions['jpylyzer'] = version
                return True
            else:
                logger.warning(
                    f"jpylyzer at {path} failed verification: "
                    f"{result.stderr.strip()}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error verifying jpylyzer at {path}: {e}")
            return False

    def is_available(self, tool: str) -> bool:
        """
        Check if a tool is available.

        Args:
            tool: Tool name

        Returns:
            bool: True if tool is available
        """
        return tool in self._available_tools

    def get_tool_path(self, tool: str) -> Optional[str]:
        """
        Get the path to a tool.

        Args:
            tool: Tool name

        Returns:
            str: Path to tool, or None if not available
        """
        return self._available_tools.get(tool)

    def get_tool_version(self, tool: str) -> Optional[str]:
        """
        Get the version of a tool.

        Args:
            tool: Tool name

        Returns:
            str: Tool version, or None if not available
        """
        return self._tool_versions.get(tool)

    def get_available_tools(self) -> Dict[str, str]:
        """
        Get all available tools and their paths.

        Returns:
            dict: Tool name -> path
        """
        return self._available_tools.copy()

    def get_tool_versions(self) -> Dict[str, str]:
        """
        Get all tool versions.

        Returns:
            dict: Tool name -> version
        """
        return self._tool_versions.copy()

    def run_tool(
        self,
        tool: str,
        args: List[str],
        timeout: Optional[int] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run a tool with the given arguments.

        Args:
            tool: Tool name
            args: Arguments for the tool
            timeout: Timeout in seconds (overrides default)
            check: Whether to raise an exception on non-zero exit codes

        Returns:
            subprocess.CompletedProcess: Process result

        Raises:
            FileNotFoundError: If tool is not available
            subprocess.TimeoutExpired: If tool timed out
            subprocess.CalledProcessError: If tool returned non-zero and check=True
        """
        if not self.is_available(tool):
            raise FileNotFoundError(f"Tool not found: {tool}")

        tool_path = self._available_tools[tool]
        timeout = timeout or self.timeout

        logger.debug(f"Running {tool} with args: {args}")

        result = subprocess.run(
            [tool_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=check
        )

        return result
