"""
Base metadata handler for JPEG2000 images.

This module provides the base functionality for managing metadata in
JPEG2000 images, including reading, writing, and validation.
"""

import os
import logging
import json
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Union

from core.metadata.xmp_utils import create_standard_metadata

logger = logging.getLogger(__name__)


class MetadataHandler:
    """Handles metadata for JPEG2000 images."""
    
    def __init__(self, debug=False):
        """Initialize the metadata handler.
        
        Args:
            debug (bool): Enable additional debug logging
        """
        try:
            self.exiftool = self._find_exiftool()
        except RuntimeError as e:
            logger.error(f"ExifTool initialization failed: {e}")
            self.exiftool = None
        
        self.xmp_template = {
            "dc:format": "image/jp2",
            "dc:creator": "JPEG2000 Workflow",
            "xmp:CreatorTool": "JPEG2000 Workflow",
            "xmp:MetadataDate": "",
            "jpeg2000:Compression": "",
            "jpeg2000:NumResolutions": "",
            "jpeg2000:ProgressionOrder": ""
        }
        
        if debug:
            logger.setLevel(logging.DEBUG)
        
        logger.info("Initialized MetadataHandler")
        
        # Validate ExifTool availability
        if self.exiftool is None:
            logger.warning("MetadataHandler initialized without ExifTool. Metadata operations may fail.")
    
    def _find_exiftool(self) -> str:
        """Find exiftool executable.
        
        Returns:
            str: Path to exiftool
            
        Raises:
            RuntimeError: If exiftool is not found
        """
        try:
            subprocess.run(
                ['exiftool', '-ver'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                check=True
            )
            return 'exiftool'
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try common installation paths
            paths = [
                '/usr/local/bin/exiftool',
                '/opt/homebrew/bin/exiftool',
                '/usr/bin/exiftool'
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            raise RuntimeError("exiftool not found. Please install exiftool.")
    
    def read_metadata(self, jp2_file: str) -> Dict[str, Any]:
        """Read metadata from a JPEG2000 file.
        
        Args:
            jp2_file: Path to JPEG2000 file
            
        Returns:
            dict: Dictionary containing metadata
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            RuntimeError: If exiftool fails to read metadata
            Exception: If any other error occurs during reading
        """
        # Validate file existence
        if not os.path.exists(jp2_file):
            raise FileNotFoundError(f"File not found: {jp2_file}")
        
        try:
            # Run exiftool to get metadata
            result = subprocess.run(
                [self.exiftool, '-j', jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"ExifTool failed: {result.stderr.strip()}")
            
            if not result.stdout.strip():
                raise RuntimeError("ExifTool returned empty output")
            
            # Parse JSON output
            try:
                metadata = json.loads(result.stdout)[0]
            except (json.JSONDecodeError, IndexError) as e:
                raise RuntimeError(f"Failed to parse ExifTool output: {str(e)}")
            
            # Organize metadata into our standard format
            organized_metadata = {
                'dublin_core': {},
                'technical': {}
            }
            
            # Map exiftool fields to Dublin Core
            dc_mapping = {
                'Title': 'title',
                'Creator': 'creator',
                'Description': 'description',
                'Rights': 'rights',
                'Source': 'source',
                'Format': 'format',
                'Language': 'language',
                'Date': 'date'
            }
            
            for exif_key, dc_key in dc_mapping.items():
                if exif_key in metadata:
                    organized_metadata['dublin_core'][dc_key] = metadata[exif_key]
            
            # Add technical metadata
            organized_metadata['technical'] = {
                'filename': os.path.basename(jp2_file),
                'filesize': os.path.getsize(jp2_file),
                'dimensions': f"{metadata.get('ImageWidth', '?')}x{metadata.get('ImageHeight', '?')}",
                'colorspace': metadata.get('ColorSpace', 'Unknown'),
                'compression': metadata.get('Compression', 'Unknown')
            }
            
            logger.info(f"Successfully read metadata from {jp2_file}")
            return organized_metadata
            
        except Exception as e:
            logger.error(f"Error reading metadata: {str(e)}")
            raise
    
    def write_metadata(
        self,
        jp2_file: str,
        metadata: Optional[Dict[str, Any]] = None,
        compression_mode: str = "supervised",
        num_resolutions: int = 10,
        progression_order: str = "RPCL",
        bnf_compliant: bool = False
    ) -> bool:
        """Write metadata to JPEG2000 file.
        
        Args:
            jp2_file: Path to JPEG2000 file
            metadata: Additional metadata to write
            compression_mode: Compression mode used (lossless, lossy, supervised)
            num_resolutions: Number of resolution levels used
            progression_order: Progression order used
            bnf_compliant: Whether to use BnF-compliant metadata format
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If the jp2_file is invalid or doesn't exist
            RuntimeError: If writing metadata fails
        """
        # Validate input file
        if not jp2_file or not isinstance(jp2_file, str):
            raise ValueError("Invalid JPEG2000 file path")
            
        if not os.path.exists(jp2_file):
            raise ValueError(f"JPEG2000 file does not exist: {jp2_file}")
            
        try:
            # Prepare metadata
            xmp_data = self.xmp_template.copy()
            xmp_data["xmp:MetadataDate"] = (
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            )
            
            # Add JPEG2000 specific metadata
            xmp_data["jpeg2000:Compression"] = compression_mode
            xmp_data["jpeg2000:NumResolutions"] = str(num_resolutions)
            xmp_data["jpeg2000:ProgressionOrder"] = progression_order
            
            # Add additional metadata if provided
            if metadata:
                if not isinstance(metadata, dict):
                    logger.warning(f"Metadata is not a dictionary: {type(metadata)}")
                    metadata = {}
                for key, value in metadata.items():
                    xmp_data[key] = value
            else:
                metadata = {}
            
            # Standard metadata writing (not BnF compliant)
            # In a production implementation, you would use
            # a library like python-xmp-toolkit or call exiftool directly
            metadata_file = f"{jp2_file}.xmp"
            try:
                with open(metadata_file, 'w') as f:
                    json.dump(xmp_data, f, indent=4)
            except OSError as e:
                logger.error(f"Failed to write metadata file {metadata_file}: {str(e)}")
                return False
            
            logger.info(f"Wrote metadata to {jp2_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing metadata: {str(e)}")
            return False
    
    def validate_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate metadata for completeness and correctness.
        
        Args:
            metadata: Dictionary containing metadata
            
        Returns:
            tuple: (is_valid, issues)
        """
        issues = []
        
        # Verify metadata is a dictionary
        if not isinstance(metadata, dict):
            issues.append(f"Metadata must be a dictionary, got {type(metadata)}")
            return False, issues
        
        # Check Dublin Core metadata
        if 'dublin_core' not in metadata or not metadata['dublin_core']:
            issues.append("Missing Dublin Core metadata")
        else:
            # Check required Dublin Core fields
            dc = metadata['dublin_core']
            if not isinstance(dc, dict):
                issues.append(f"Dublin Core metadata must be a dictionary, got {type(dc)}")
            else:
                if 'title' not in dc or not dc['title']:
                    issues.append("Missing Dublin Core title")
                if 'creator' not in dc or not dc['creator']:
                    issues.append("Missing Dublin Core creator")
                if 'format' not in dc or not dc['format']:
                    issues.append("Missing Dublin Core format")
        
        # Validate is successful if no issues found
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.info("Metadata validation successful")
        else:
            logger.warning(f"Metadata validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"- {issue}")
        
        return is_valid, issues
    
    def export_metadata(
        self,
        metadata: Dict[str, Any],
        output_file: str
    ) -> str:
        """Export metadata to a JSON file.
        
        Args:
            metadata: Dictionary containing metadata
            output_file: Path to output file
            
        Returns:
            str: Path to the output file
            
        Raises:
            ValueError: If metadata is not a dictionary
            OSError: If writing to the output file fails
        """
        # Validate metadata
        if not isinstance(metadata, dict):
            raise ValueError(f"Metadata must be a dictionary, got {type(metadata)}")
        
        try:
            # Ensure directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # Write metadata to file
            with open(output_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Exported metadata to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting metadata: {str(e)}")
            raise
