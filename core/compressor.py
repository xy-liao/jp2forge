"""
JP2Forge Compressor module for image compression.

This module provides the core functionality for compressing images
to JPEG2000 format with various quality settings.
"""

import os
import logging
import gc
import subprocess
import math
import numpy as np
from PIL import Image
from typing import Dict, Any, Optional, Union, Tuple, List

from core.types import DocumentType, CompressionMode, BnFCompressionRatio

logger = logging.getLogger(__name__)


class JPEG2000Compressor:
    """Handles JPEG2000 compression operations.

    This is an original implementation that uses either Pillow's JPEG2000 support
    or optionally Kakadu (if available) for BnF compliance. It is not based on or
    derived from other implementations like OpenJPEG.
    """

    def __init__(
        self,
        num_resolutions: int = 10,
        progression_order: str = "RPCL",
        chunk_size: int = 1000000,  # Default 1M pixels per chunk
        memory_limit_mb: int = 4096,  # Default 4GB memory limit
        use_kakadu: bool = False,  # Whether to use Kakadu for BnF compliance
        kakadu_path: str = "kdu_compress"  # Path to Kakadu executable
    ):
        """Initialize the compressor.

        Args:
            num_resolutions: Number of resolution levels
            progression_order: Progression order for JPEG2000
            chunk_size: Number of pixels to process at once for large images
            memory_limit_mb: Memory limit in MB for adaptive processing
            use_kakadu: Whether to use Kakadu for BnF compliance
            kakadu_path: Path to Kakadu executable
        """
        self.num_resolutions = num_resolutions
        self.progression_order = progression_order
        self.chunk_size = chunk_size
        self.memory_limit_mb = memory_limit_mb
        self.use_kakadu = use_kakadu
        self.kakadu_path = kakadu_path

    def convert_to_jp2(
        self,
        input_file: str,
        output_file: str,
        doc_type: DocumentType,
        compression_mode: CompressionMode = CompressionMode.SUPERVISED,
        lossless_fallback: bool = True,
        bnf_compliant: bool = False,
        compression_ratio_tolerance: float = 0.05,
        include_bnf_markers: bool = True
    ) -> bool:
        """Convert image to JPEG2000 format.

        Args:
            input_file: Path to input image
            output_file: Path for output JP2 file
            doc_type: Type of document being processed
            compression_mode: Compression mode to use
            lossless_fallback: Whether to fall back to lossless compression
            bnf_compliant: Whether to use BnF compliant settings
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers

        Returns:
            bool: True if conversion successful

        Raises:
            FileNotFoundError: If input file doesn't exist
            RuntimeError: If conversion fails critically
        """
        # Validate input file
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file does not exist: {input_file}")

        try:
            # Determine if we need to use lossless compression
            use_lossless = (compression_mode == CompressionMode.LOSSLESS)

            # If BnF compliant or using Kakadu, use special processing path
            if bnf_compliant or (compression_mode == CompressionMode.BNF_COMPLIANT) or self.use_kakadu:
                success = self._convert_bnf_compliant(
                    input_file,
                    output_file,
                    doc_type,
                    use_lossless,
                    compression_ratio_tolerance,
                    include_bnf_markers
                )
                if not success and lossless_fallback and not use_lossless:
                    logger.info("BnF compliant conversion failed, falling back to lossless...")
                    return self.convert_to_jp2(
                        input_file,
                        output_file,
                        doc_type,
                        CompressionMode.LOSSLESS,
                        False,  # No further fallback
                        bnf_compliant,
                        compression_ratio_tolerance,
                        include_bnf_markers
                    )
                return success
            else:
                # Check if we need to process in chunks
                from utils.image import should_process_in_chunks
                should_chunk, chunk_size = should_process_in_chunks(
                    input_file, self.memory_limit_mb)

                if should_chunk:
                    return self._convert_to_jp2_chunked(
                        input_file,
                        output_file,
                        doc_type,
                        use_lossless,
                        chunk_size or self.chunk_size
                    )
                else:
                    # Regular processing path (using Pillow)
                    try:
                        with Image.open(input_file) as img:
                            # Ensure color profile is compatible with JPEG2000
                            from utils.color_profiles import ensure_jp2_compatible_profile
                            img = ensure_jp2_compatible_profile(img)

                            # Configure compression parameters based on document type
                            params = self._get_compression_params(doc_type, use_lossless)

                            # Convert to JPEG2000
                            img.save(
                                output_file,
                                format="JPEG2000",
                                **params
                            )
                    except OSError as e:
                        logger.error(f"Failed to open or process image: {str(e)}")
                        raise

            # Force garbage collection
            gc.collect()

            return True

        except Exception as e:
            logger.error(f"Error converting {input_file}: {str(e)}")

            # Try lossless fallback if enabled and not already using lossless
            if lossless_fallback and compression_mode != CompressionMode.LOSSLESS:
                logger.info("Attempting lossless fallback...")
                return self.convert_to_jp2(
                    input_file,
                    output_file,
                    doc_type,
                    CompressionMode.LOSSLESS,
                    lossless_fallback=False,
                    bnf_compliant=bnf_compliant,
                    compression_ratio_tolerance=compression_ratio_tolerance,
                    include_bnf_markers=include_bnf_markers
                )

            # If error is critical and fallback didn't work, propagate it
            if isinstance(e, (FileNotFoundError, PermissionError, OSError)):
                raise

            return False

    def _convert_to_jp2_chunked(
        self,
        input_file: str,
        output_file: str,
        doc_type: DocumentType,
        lossless: bool,
        rows_per_chunk: int
    ) -> bool:
        """
        Convert large image to JPEG2000 by processing in chunks.

        Args:
            input_file: Path to input image
            output_file: Path for output JP2 file
            doc_type: Type of document being processed
            lossless: Whether to use lossless compression
            rows_per_chunk: Number of rows to process at once

        Returns:
            bool: True if conversion successful
        """
        try:
            logger.info(f"Processing {input_file} in chunks")

            # Open the image to get dimensions and mode
            with Image.open(input_file) as img:
                width, height = img.size
                mode = img.mode

                # Calculate number of chunks needed
                num_chunks = math.ceil(height / rows_per_chunk)
                logger.info(f"Image size: {width}x{height}, processing in {num_chunks} chunks")

                # Use a temporary buffer for each piece
                temp_pieces = []

                # Process image in chunks
                for i in range(num_chunks):
                    start_row = i * rows_per_chunk
                    end_row = min((i + 1) * rows_per_chunk, height)
                    current_rows = end_row - start_row

                    # Create a box for cropping (left, upper, right, lower)
                    box = (0, start_row, width, end_row)

                    # Create a temporary file for this chunk
                    temp_file = f"{output_file}_chunk_{i}.jp2"
                    temp_pieces.append(temp_file)

                    # Process this chunk
                    with img.crop(box) as chunk:
                        logger.info(
                            f"Processing chunk {i+1}/{num_chunks}: rows {start_row}-{end_row}")

                        # Configure compression parameters
                        params = self._get_compression_params(doc_type, lossless)

                        # Save chunk
                        chunk.save(temp_file, format="JPEG2000", **params)

                    # Force garbage collection after each chunk
                    gc.collect()

                # Now we need to merge the pieces into a single JP2 file
                # This is challenging since JP2 doesn't have a standard way to concatenate images
                # For now, we'll reconstruct by reading the chunks and creating a new image

                # First, create a destination image with the right dimensions
                merged_img = Image.new(mode, (width, height))

                # Paste each chunk into the right position
                for i, temp_file in enumerate(temp_pieces):
                    start_row = i * rows_per_chunk

                    try:
                        with Image.open(temp_file) as chunk:
                            # Calculate position for pasting
                            box = (0, start_row)
                            merged_img.paste(chunk, box)
                    except Exception as e:
                        logger.error(f"Error reading chunk {i}: {str(e)}")
                        return False

                # Save the merged image
                params = self._get_compression_params(doc_type, lossless)
                merged_img.save(output_file, format="JPEG2000", **params)

                # Clean up temporary files
                for temp_file in temp_pieces:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")

                return True

        except Exception as e:
            logger.error(f"Error in chunked conversion: {str(e)}")

            # Clean up any temporary files that might exist
            try:
                for i in range(1000):  # Arbitrary large number
                    temp_file = f"{output_file}_chunk_{i}.jp2"
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    else:
                        break
            except Exception:
                pass

            return False

    def _get_compression_params(
        self,
        doc_type: DocumentType,
        lossless: bool,
        bnf_compliant: bool = False
    ) -> dict:
        """Get compression parameters based on document type.

        Args:
            doc_type: Type of document being processed
            lossless: Whether to use lossless compression
            bnf_compliant: Whether to use BnF compliant parameters

        Returns:
            dict: Compression parameters
        """
        params = {
            "num_resolutions": self.num_resolutions,
            "progression": self.progression_order,
            "irreversible": not lossless,
        }

        if bnf_compliant:
            # Add BnF-specific parameters
            params.update({
                "codeblock_size": (64, 64),  # BnF uses 64x64 codeblocks
                "tile_size": (1024, 1024),  # BnF uses 1024x1024 tiles
            })

        if doc_type == DocumentType.PHOTOGRAPH:
            params.update({
                "quality_mode": "rates",
                "quality_layers": [60, 40, 20]
            })
        elif doc_type == DocumentType.HERITAGE_DOCUMENT:
            params.update({
                "quality_mode": "dB",
                "quality_layers": [45, 40, 35]
            })
        elif doc_type == DocumentType.COLOR:
            params.update({
                "quality_mode": "rates",
                "quality_layers": [50, 30, 10]
            })
        elif doc_type == DocumentType.GRAYSCALE:
            params.update({
                "quality_mode": "rates",
                "quality_layers": [40, 30, 20]
            })
        else:  # Default parameters
            params.update({
                "quality_mode": "rates",
                "quality_layers": [50, 30, 10]
            })

        return params

    def _convert_bnf_compliant(
        self,
        input_file: str,
        output_file: str,
        doc_type: DocumentType,
        lossless: bool,
        compression_ratio_tolerance: float = 0.05,
        include_bnf_markers: bool = True
    ) -> bool:
        """
        Convert image to JPEG2000 format using BnF compliant settings.

        Args:
            input_file: Path to input image
            output_file: Path for output JP2 file
            doc_type: Type of document being processed
            lossless: Whether to use lossless compression
            compression_ratio_tolerance: Tolerance for compression ratio
            include_bnf_markers: Whether to include BnF robustness markers

        Returns:
            bool: True if conversion successful
        """
        try:
            # Get BnF compression ratio for document type
            target_ratio = BnFCompressionRatio.get_ratio_for_type(doc_type)

            # If using Kakadu, use it for BnF compliant conversion
            if self.use_kakadu:
                return self._convert_with_kakadu(
                    input_file,
                    output_file,
                    target_ratio,
                    lossless,
                    include_bnf_markers
                )

            # Check if we need to process in chunks
            from utils.image import should_process_in_chunks
            should_chunk, chunk_size = should_process_in_chunks(input_file, self.memory_limit_mb)

            if should_chunk:
                logger.info(f"Large image detected, using chunked processing for BnF compliance")
                success = self._convert_to_jp2_chunked(
                    input_file,
                    output_file,
                    doc_type,
                    lossless,
                    chunk_size or self.chunk_size
                )

                # Check compression ratio if successful
                if success and not lossless:
                    ratio_ok = self._check_compression_ratio(
                        input_file,
                        output_file,
                        target_ratio,
                        compression_ratio_tolerance
                    )

                    if not ratio_ok:
                        logger.warning(
                            f"Compression ratio outside acceptable range for {input_file}")
                        return False

                return success

            # Otherwise use Pillow with BnF-compliant settings
            with Image.open(input_file) as img:
                # Ensure color profile is compatible with JPEG2000
                from utils.color_profiles import ensure_jp2_compatible_profile
                img = ensure_jp2_compatible_profile(img)

                # Get basic parameters
                params = {
                    "num_resolutions": self.num_resolutions,
                    "progression": self.progression_order,
                    "irreversible": not lossless,
                    "quality_mode": "rates",
                }

                # Add BnF robustness markers if requested
                if include_bnf_markers:
                    # Note: Pillow doesn't directly support SOP, EPH, PLT markers
                    # but we'll add what we can through parameters
                    params.update({
                        "codeblock_size": (64, 64),  # BnF uses 64x64 codeblocks
                        "tile_size": (1024, 1024),  # BnF uses 1024x1024 tiles
                    })

                # Make a best effort to target the correct compression ratio
                if not lossless:
                    if doc_type == DocumentType.PHOTOGRAPH or doc_type == DocumentType.HERITAGE_DOCUMENT:
                        params["quality_layers"] = [80, 60, 40, 20]
                    elif doc_type == DocumentType.COLOR:
                        params["quality_layers"] = [70, 50, 30, 15]
                    elif doc_type == DocumentType.GRAYSCALE:
                        params["quality_layers"] = [60, 40, 20]

                # Save with BnF-compliant parameters
                img.save(output_file, format="JPEG2000", **params)

                # Check if compression ratio is within acceptable range
                if not lossless:
                    ratio_ok = self._check_compression_ratio(
                        input_file,
                        output_file,
                        target_ratio,
                        compression_ratio_tolerance
                    )

                    if not ratio_ok:
                        logger.warning(
                            f"Compression ratio outside acceptable range for {input_file}")
                        return False

                return True

        except Exception as e:
            logger.error(f"Error in BnF compliant conversion: {str(e)}")
            return False

    def _convert_with_kakadu(
        self,
        input_file: str,
        output_file: str,
        target_ratio: float,
        lossless: bool,
        include_bnf_markers: bool = True
    ) -> bool:
        """
        Convert image to JPEG2000 using Kakadu for BnF compliance.

        Args:
            input_file: Path to input image
            output_file: Path for output JP2 file
            target_ratio: Target compression ratio
            lossless: Whether to use lossless compression
            include_bnf_markers: Whether to include BnF robustness markers

        Returns:
            bool: True if conversion successful

        Raises:
            FileNotFoundError: If Kakadu is not found
            RuntimeError: If Kakadu fails
        """
        # Verify Kakadu is available
        if not os.path.exists(self.kakadu_path) and not self._is_command_available(self.kakadu_path):
            raise FileNotFoundError(f"Kakadu executable not found: {self.kakadu_path}")

        try:
            # Build Kakadu command
            cmd = [self.kakadu_path]

            # Input and output
            cmd.extend(["-i", input_file, "-o", output_file])

            # Basic parameters
            num_threads = max(1, os.cpu_count() - 1)
            cmd.extend([f"-num_threads={num_threads}", "-quiet"])

            # Resolution levels
            cmd.append(f"Clevels={self.num_resolutions}")

            # Compression type
            if lossless:
                cmd.append("Creversible=yes")
            else:
                cmd.append("Creversible=no")

                # Calculate rate based on target ratio
                # For 24-bit color images, rate = 24/target_ratio
                with Image.open(input_file) as img:
                    if img.mode in ["RGB", "RGBA"]:
                        bit_depth = 24
                    else:  # Grayscale
                        bit_depth = 8

                rate = bit_depth / target_ratio
                cmd.append(f"-rate {rate}")

            # Progression order - RPCL is BnF standard
            cmd.append("Corder=RPCL")

            # Add BnF robustness markers
            if include_bnf_markers:
                cmd.extend([
                    "Stiles={1024,1024}",
                    "Cblk={64,64}",
                    "Cuse_sop=yes",
                    "Cuse_eph=yes",
                    "ORGgen_plt=yes",
                    "ORGtparts=R",
                    "Cprecincts={256,256},{256,256},{128,128}",
                ])

            cmd.append("-precise")

            # Execute command
            logger.info(f"Running Kakadu: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or f"Exit code: {result.returncode}"
                logger.error(f"Kakadu error: {error_msg}")
                raise RuntimeError(f"Kakadu failed: {error_msg}")

            # Check if output file exists and has content
            if not os.path.exists(output_file):
                raise RuntimeError("Kakadu did not produce an output file")

            if os.path.getsize(output_file) == 0:
                os.remove(output_file)  # Clean up empty file
                raise RuntimeError("Kakadu produced an empty output file")

            # Check compression ratio if not lossless
            if not lossless:
                ratio_ok = self._check_compression_ratio(
                    input_file,
                    output_file,
                    target_ratio,
                    0.05  # 5% tolerance per BnF spec
                )

                if not ratio_ok:
                    logger.warning(f"Compression ratio outside acceptable range for {input_file}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error with Kakadu conversion: {str(e)}")

            # Clean up any partial output file
            if os.path.exists(output_file):
                try:
                    os.remove(output_file)
                except Exception:
                    pass

            # Re-raise critical errors
            if isinstance(e, (FileNotFoundError, RuntimeError)):
                raise

            return False

    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in the system path.

        Args:
            command: Command to check

        Returns:
            bool: True if command is available
        """
        try:
            subprocess.run(
                [command, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            return True
        except FileNotFoundError:
            return False

    def _check_compression_ratio(
        self,
        original_file: str,
        compressed_file: str,
        target_ratio: float,
        tolerance: float = 0.05
    ) -> bool:
        """
        Verify if compression ratio is within acceptable limits.

        Args:
            original_file: Path to original file
            compressed_file: Path to compressed file
            target_ratio: Target compression ratio (e.g., 4.0 for 1:4)
            tolerance: Tolerance percentage (default 5%)

        Returns:
            bool: True if within acceptable range
        """
        try:
            # Check if files exist
            if not os.path.exists(original_file):
                logger.error(f"Original file not found: {original_file}")
                return False

            if not os.path.exists(compressed_file):
                logger.error(f"Compressed file not found: {compressed_file}")
                return False

            orig_size = os.path.getsize(original_file)
            comp_size = os.path.getsize(compressed_file)

            if comp_size == 0:
                logger.error(f"Compressed file is empty: {compressed_file}")
                return False

            actual_ratio = orig_size / comp_size
            min_ratio = target_ratio * (1 - tolerance)
            max_ratio = target_ratio * (1 + tolerance)

            logger.info(f"Compression ratio check: target={target_ratio}, actual={actual_ratio:.2f}, "
                        f"range=[{min_ratio:.2f}, {max_ratio:.2f}]")

            return min_ratio <= actual_ratio <= max_ratio

        except Exception as e:
            logger.error(f"Error checking compression ratio: {str(e)}")
            return False

    def get_recommended_settings(
        self,
        input_file: str,
        doc_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Get recommended compression settings for an image.

        Args:
            input_file: Path to input image
            doc_type: Type of document

        Returns:
            dict: Recommended settings
        """
        try:
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"Input file not found: {input_file}")

            with Image.open(input_file) as img:
                width, height = img.size
                num_pixels = width * height

                # Check if file is unusually large or small
                if width <= 0 or height <= 0:
                    raise ValueError(f"Invalid image dimensions: {width}x{height}")

                # Get color depth information
                mode = img.mode
                color_info = ""
                if mode in ["L", "P", "1"]:
                    color_info = "grayscale or indexed"
                elif mode in ["RGB", "RGBA"]:
                    color_info = "full color"
                else:
                    color_info = f"special mode ({mode})"

                # Base recommendations on image size, type and color information
                if num_pixels > 50000000:  # >50MP
                    # For very large images
                    return {
                        "num_resolutions": 12,
                        "progression_order": "RPCL",  # Changed to RPCL for BnF compatibility
                        "compression_mode": CompressionMode.BNF_COMPLIANT.value,
                        "tile_size": 1024,
                        "quality_layers": 5,
                        "chunked_processing": True,
                        "memory_required_mb": int(num_pixels * 12 / (1024 * 1024)),
                        "notes": f"Large image ({width}x{height}, {color_info}) with BnF compliant settings. Consider chunked processing."
                    }
                elif num_pixels > 10000000:  # >10MP
                    # For medium-large images
                    return {
                        "num_resolutions": 10,  # BnF standard
                        "progression_order": "RPCL",
                        "compression_mode": CompressionMode.BNF_COMPLIANT.value,
                        "tile_size": 1024,  # BnF standard
                        "quality_layers": 3,
                        "chunked_processing": False,
                        "memory_required_mb": int(num_pixels * 8 / (1024 * 1024)),
                        "notes": f"Medium-large image ({width}x{height}, {color_info}) with BnF compliant settings"
                    }
                else:
                    # For smaller images
                    return {
                        "num_resolutions": 10,  # BnF standard
                        "progression_order": "RPCL",
                        "compression_mode": CompressionMode.BNF_COMPLIANT.value,
                        "tile_size": 1024,  # BnF standard
                        "quality_layers": 3,
                        "chunked_processing": False,
                        "memory_required_mb": int(num_pixels * 4 / (1024 * 1024)),
                        "notes": f"Standard image ({width}x{height}, {color_info}) with BnF compliant settings"
                    }

        except Exception as e:
            logger.error(f"Error getting recommended settings: {str(e)}")
            # Return default settings on error
            return {
                "num_resolutions": 10,
                "progression_order": "RPCL",
                "compression_mode": CompressionMode.BNF_COMPLIANT.value,
                "tile_size": 1024,
                "quality_layers": 3,
                "chunked_processing": False,
                "memory_required_mb": 1024,
                "notes": f"Default BnF compliant settings (error encountered: {str(e)})"
            }
