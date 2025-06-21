"""
ExifTool interface for JP2Forge.

This module provides a wrapper for ExifTool to read and write
metadata in image files, particularly for JPEG2000 XMP metadata.
"""

import os
import json
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, List, Union, Tuple, BinaryIO
from ..security import validate_tool_path, validate_file_path, validate_subprocess_args

logger = logging.getLogger(__name__)


class ExifTool:
    """
    Interface for ExifTool metadata operations.

    This class provides methods for reading and writing metadata
    in image files, with particular focus on XMP metadata for
    JPEG2000 files.
    """

    def __init__(
        self,
        exiftool_path: str,
        temp_dir: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize the ExifTool interface.

        Args:
            exiftool_path: Path to exiftool executable
            temp_dir: Directory for temporary files
            timeout: Timeout for command execution in seconds
        """
        self.exiftool_path = exiftool_path
        self.temp_dir = temp_dir
        self.timeout = timeout

        # Validate ExifTool path using security validation
        if not validate_tool_path(exiftool_path, "exiftool"):
            raise FileNotFoundError(f"ExifTool validation failed: {exiftool_path}")

        logger.info(f"Initialized ExifTool interface with exiftool at {exiftool_path}")

    def get_version(self) -> str:
        """
        Get ExifTool version information.

        Returns:
            str: Version information
        """
        try:
            result = subprocess.run(
                [self.exiftool_path, '-ver'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.warning(f"ExifTool version check failed: {result.stderr.strip()}")
                return "Unknown version"

        except Exception as e:
            logger.error(f"Error getting ExifTool version: {e}")
            return "Error retrieving version"

    def read_metadata(
        self,
        file_path: str,
        tags: Optional[List[str]] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Read metadata from a file.

        Args:
            file_path: Path to file
            tags: Specific tags to read (None for all)
            format: Output format ('json', 'xml', 'html')

        Returns:
            dict: Metadata dictionary
        """
        # Validate file path
        if not validate_file_path(file_path):
            raise FileNotFoundError(f"File validation failed: {file_path}")
            
        try:
            # Build command
            cmd = [self.exiftool_path]

            # Add format options
            if format == 'json':
                cmd.append('-j')
            elif format == 'xml':
                cmd.append('-X')
            elif format == 'html':
                cmd.append('-h')

            # Add specific tags if requested
            if tags:
                for tag in tags:
                    cmd.append(f"-{tag}")

            # Add file path
            cmd.append(file_path)
            
            # Validate command arguments
            if not validate_subprocess_args(cmd):
                raise ValueError("Invalid command arguments detected")

            # Run command
            logger.debug(f"Running ExifTool command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            # Check for errors
            if result.returncode != 0:
                logger.error(
                    f"ExifTool failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return {'error': result.stderr.strip()}

            # Parse output based on format
            if format == 'json':
                try:
                    data = json.loads(result.stdout)
                    return data[0] if data else {}
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing ExifTool JSON output: {e}")
                    return {'error': f"JSON parse error: {e}"}
            else:
                # Return raw output for other formats
                return {'raw': result.stdout}

        except Exception as e:
            logger.error(f"Error running ExifTool: {e}")
            return {'error': str(e)}

    def write_metadata(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        overwrite_original: bool = True
    ) -> bool:
        """
        Write metadata to a file.

        Args:
            file_path: Path to file
            metadata: Metadata to write
            overwrite_original: Whether to overwrite the original file

        Returns:
            bool: True if successful
        """
        try:
            # Create temporary file for metadata
            fd, temp_path = tempfile.mkstemp(
                suffix='.json',
                prefix='exiftool_',
                dir=self.temp_dir
            )

            try:
                # Write metadata to temporary file
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f)

                # Build command
                cmd = [self.exiftool_path]

                # Add options
                if overwrite_original:
                    cmd.append('-overwrite_original')

                # Add metadata file
                cmd.extend(['-json', temp_path])

                # Add target file
                cmd.append(file_path)

                # Run command
                logger.debug(f"Running ExifTool command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )

                # Check for errors
                if result.returncode != 0:
                    logger.error(
                        f"ExifTool write failed with code {result.returncode}: "
                        f"{result.stderr.strip()}"
                    )
                    return False

                logger.info(f"Successfully wrote metadata to {file_path}")
                return True

            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

        except Exception as e:
            logger.error(f"Error writing metadata: {e}")
            return False

    def write_xmp_block(
        self,
        file_path: str,
        xmp_content: str,
        overwrite_original: bool = True
    ) -> bool:
        """
        Write XMP metadata block to a file.

        Args:
            file_path: Path to file
            xmp_content: XMP metadata as XML string
            overwrite_original: Whether to overwrite the original file

        Returns:
            bool: True if successful
        """
        try:
            # Create temporary file for XMP content
            fd, temp_path = tempfile.mkstemp(
                suffix='.xmp',
                prefix='exiftool_',
                dir=self.temp_dir
            )

            try:
                # Write XMP content to temporary file
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(xmp_content)

                # Build command
                cmd = [self.exiftool_path]

                # Add options
                if overwrite_original:
                    cmd.append('-overwrite_original')

                # Add XMP file
                cmd.extend(['-xmp', f"<={temp_path}"])

                # Add target file
                cmd.append(file_path)

                # Run command
                logger.debug(f"Running ExifTool command: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )

                # Check for errors
                if result.returncode != 0:
                    logger.error(
                        f"ExifTool XMP write failed with code {result.returncode}: "
                        f"{result.stderr.strip()}"
                    )
                    return False

                logger.info(f"Successfully wrote XMP metadata to {file_path}")
                return True

            finally:
                # Clean up temporary file
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

        except Exception as e:
            logger.error(f"Error writing XMP metadata: {e}")
            return False

    def extract_xmp(self, file_path: str) -> str:
        """
        Extract XMP metadata from a file.

        Args:
            file_path: Path to file

        Returns:
            str: XMP metadata as XML string
        """
        try:
            # Build command
            cmd = [self.exiftool_path, '-xmp', '-b', file_path]

            # Run command
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            # Check for errors
            if result.returncode != 0:
                logger.error(
                    f"ExifTool XMP extraction failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return ""

            return result.stdout

        except Exception as e:
            logger.error(f"Error extracting XMP metadata: {e}")
            return ""

    def copy_metadata(
        self,
        source_file: str,
        target_file: str,
        tags: Optional[List[str]] = None,
        overwrite_original: bool = True
    ) -> bool:
        """
        Copy metadata from one file to another.

        Args:
            source_file: Source file path
            target_file: Target file path
            tags: Specific tags to copy (None for all)
            overwrite_original: Whether to overwrite the original target file

        Returns:
            bool: True if successful
        """
        try:
            # Build command
            cmd = [self.exiftool_path]

            # Add options
            if overwrite_original:
                cmd.append('-overwrite_original')

            # Add specific tags if requested
            if tags:
                for tag in tags:
                    cmd.append(f"-{tag}")
            else:
                cmd.append('-all')

            # Add target specification
            cmd.append(f"-tagsFromFile")
            cmd.append(source_file)

            # Add target file
            cmd.append(target_file)

            # Run command
            logger.debug(f"Running ExifTool command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            # Check for errors
            if result.returncode != 0:
                logger.error(
                    f"ExifTool metadata copy failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return False

            logger.info(f"Successfully copied metadata from {source_file} to {target_file}")
            return True

        except Exception as e:
            logger.error(f"Error copying metadata: {e}")
            return False
