"""
Kakadu interface for JP2Forge.

This module provides a wrapper for Kakadu's kdu_compress and related tools
to generate JPEG2000 files according to BnF specifications.

EXPERIMENTAL: This integration is currently conceptual and has not been tested
with actual Kakadu software.
"""

import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class KakaduTool:
    """
    EXPERIMENTAL: Interface for Kakadu JPEG2000 tools.

    This class provides methods for creating JPEG2000 files
    using Kakadu software, with support for BnF-specific
    parameters.

    Note: This integration is conceptual and has never been tested
    with actual Kakadu software. It remains as a reference implementation
    for how BnF-compliant JP2 files might be created using Kakadu.
    """

    def __init__(
        self,
        kdu_compress_path: str,
        temp_dir: Optional[str] = None,
        timeout: int = 300
    ):
        """
        Initialize the Kakadu tool interface.

        Args:
            kdu_compress_path: Path to kdu_compress executable
            temp_dir: Directory for temporary files
            timeout: Timeout for command execution in seconds
        """
        self.kdu_compress_path = kdu_compress_path
        self.temp_dir = temp_dir
        self.timeout = timeout

        # Validate existence of Kakadu tools
        if not os.path.exists(kdu_compress_path):
            raise FileNotFoundError(f"kdu_compress not found at: {kdu_compress_path}")

        # Find Kakadu directory
        self.kakadu_dir = os.path.dirname(kdu_compress_path)

        logger.info(f"Initialized KakaduTool with kdu_compress at {kdu_compress_path}")

    def get_version(self) -> str:
        """
        Get Kakadu version information.

        Returns:
            str: Version information
        """
        try:
            result = subprocess.run(
                [self.kdu_compress_path, '-v'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            # Kakadu outputs version to stderr
            output = result.stderr.strip() or result.stdout.strip()

            # Extract version if possible
            for line in output.split('\n'):
                if 'Version' in line:
                    return line.strip()

            return "Unknown version"

        except Exception as e:
            logger.error(f"Error getting Kakadu version: {e}")
            return "Error retrieving version"

    def compress_image(
        self,
        input_file: str,
        output_file: str,
        parameters: Optional[Dict[str, Any]] = None,
        verbose: bool = False
    ) -> bool:
        """
        Compress an image using kdu_compress.

        Args:
            input_file: Path to input image
            output_file: Path to output JP2 file
            parameters: Additional parameters for kdu_compress
            verbose: Enable verbose output

        Returns:
            bool: True if successful
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Build command
            cmd = [self.kdu_compress_path]

            # Add input/output
            cmd.extend(['-i', input_file, '-o', output_file])

            # Add parameters if provided
            if parameters:
                for key, value in parameters.items():
                    if key.startswith('-'):
                        # Parameter with prefix
                        cmd.append(key)
                        if value is not None:
                            cmd.append(str(value))
                    else:
                        # Parameter without prefix
                        cmd.append(f"{key}={value}")

            # Run command
            logger.debug(f"Running Kakadu command: {' '.join(cmd)}")

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
                    f"kdu_compress failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return False

            if verbose:
                logger.info(f"kdu_compress output: {result.stdout.strip()}")
                if result.stderr:
                    logger.info(f"kdu_compress stderr: {result.stderr.strip()}")

            logger.info(f"Successfully compressed {input_file} to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Error running kdu_compress: {e}")
            return False

    def create_bnf_compliant_jp2(
        self,
        input_file: str,
        output_file: str,
        uuid_box_file: Optional[str] = None,
        num_threads: int = 0,
        compression_ratio: float = 4.0,
        num_levels: int = 10,
        use_precise: bool = True,
        verbose: bool = False
    ) -> bool:
        """
        Create a BnF-compliant JPEG2000 file.

        Args:
            input_file: Path to input image
            output_file: Path to output JP2 file
            uuid_box_file: Path to file containing UUID box data
            num_threads: Number of threads to use (0 for auto)
            compression_ratio: Target compression ratio
            num_levels: Number of resolution levels
            use_precise: Use precise rate control
            verbose: Enable verbose output

        Returns:
            bool: True if successful
        """
        try:
            # Calculate rate parameter
            # For 24-bit RGB image with 1:4 ratio, rate = 6.0
            # (24 bits / 4 = 6 bits/sample)
            rate = (24 / compression_ratio)

            # Build BnF-compliant parameters
            params = {
                '-rate': f"{rate:.1f}",
                'Clayers': 10,
                'Creversible': 'no',
                'Clevels': num_levels,
                'Stiles': '{1024,1024}',
                'Cblk': '{64,64}',
                'Corder': 'RPCL',
                'ORGtparts': 'R',
                'Cprecincts': '{256,256},{256,256},{128,128}',
                'Cuse_sop': 'yes',
                'Cuse_eph': 'yes',
                'ORGgen_plt': 'yes',
            }

            # Add UUID box if provided
            if uuid_box_file:
                params['-jp2_box'] = uuid_box_file

            # Add precise rate control if requested
            if use_precise:
                params['-precise'] = None

            # Add thread count if specified
            if num_threads > 0:
                params['-num_threads'] = num_threads

            # Run compression
            return self.compress_image(
                input_file, output_file, params, verbose
            )

        except Exception as e:
            logger.error(f"Error creating BnF-compliant JP2: {e}")
            return False

    def create_uuid_box_file(
        self,
        metadata_xml: str
    ) -> str:
        """
        Create a temporary file containing UUID box data.

        Args:
            metadata_xml: XMP metadata XML

        Returns:
            str: Path to temporary file
        """
        try:
            # Create temporary file
            fd, temp_path = tempfile.mkstemp(
                suffix='.uuid',
                prefix='jp2forge_',
                dir=self.temp_dir
            )

            # Write 'uuid' identifier followed by metadata
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write("uuid\n")
                f.write(metadata_xml)

            logger.debug(f"Created UUID box file at {temp_path}")
            return temp_path

        except Exception as e:
            logger.error(f"Error creating UUID box file: {e}")
            raise

    def analyze_jp2(self, jp2_file: str) -> Dict[str, Any]:
        """
        Analyze a JPEG2000 file for quality and correctness.

        This requires kdu_jp2info or similar tool from Kakadu.

        Args:
            jp2_file: Path to JPEG2000 file

        Returns:
            dict: File analysis information
        """
        # Find kdu_jp2info if available
        kdu_jp2info = os.path.join(self.kakadu_dir, 'kdu_jp2info')
        if not os.path.exists(kdu_jp2info):
            kdu_jp2info = os.path.join(self.kakadu_dir, 'kdu_jp2info.exe')
            if not os.path.exists(kdu_jp2info):
                logger.warning("kdu_jp2info not found, cannot analyze JP2 file")
                return {'error': 'kdu_jp2info not found'}

        try:
            # Run kdu_jp2info
            result = subprocess.run(
                [kdu_jp2info, jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout,
                check=False
            )

            if result.returncode != 0:
                logger.error(
                    f"kdu_jp2info failed with code {result.returncode}: "
                    f"{result.stderr.strip()}"
                )
                return {'error': result.stderr.strip()}

            # Parse output
            info = {}
            current_section = 'general'
            info[current_section] = {}

            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Check for section header
                if line.endswith(':') and not ': ' in line:
                    current_section = line[:-1].lower()
                    info[current_section] = {}
                    continue

                # Parse key-value pair
                if ': ' in line:
                    key, value = line.split(': ', 1)
                    info[current_section][key.strip()] = value.strip()

            return info

        except Exception as e:
            logger.error(f"Error analyzing JP2 file: {e}")
            return {'error': str(e)}
