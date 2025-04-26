"""
BnF-compliant metadata handler for JPEG2000 images.

This module provides functionality for managing BnF-compliant metadata
in JPEG2000 images, implementing the technical specifications published by
the Bibliothèque nationale de France (BnF). This implementation is provided
for educational and training purposes, demonstrating how to implement the
BnF's XMP metadata requirements described in their "Référentiel de format de
fichier image v2" (2015).

See: https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf
"""

import os
import logging
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List, Union

from core.metadata.base_handler import MetadataHandler

logger = logging.getLogger(__name__)


class BnFMetadataHandler(MetadataHandler):
    """Handles BnF-compliant metadata for JPEG2000 images.
    
    This class implements the BnF technical specifications for metadata
    in JPEG2000 files for educational and training purposes. The implementation
    is based on the BnF reference document "Référentiel de format de fichier image v2"
    (2015). The technical parameters are implemented from this specification, but
    the code and implementation approach are original work.
    
    This is an independent implementation that does not use, incorporate, or 
    derive from other implementations like OpenJPEG. It uses standard Python 
    libraries and ExifTool for metadata manipulation.
    """
    
    def __init__(self, base_handler=None, debug=False):
        """Initialize the BnF metadata handler.
        
        Args:
            base_handler (MetadataHandler, optional): Optional base metadata handler
            debug (bool): Enable additional debug logging
        """
        # Ensure we have a base metadata handler
        if base_handler is None:
            from core.metadata.base_handler import MetadataHandler
            base_handler = MetadataHandler(debug=debug)
        
        # Call parent's init with base handler
        super().__init__()
        
        # Add additional checks to verify ExifTool availability
        if not base_handler.exiftool:
            logger.error("BnFMetadataHandler initialized without ExifTool")
        
        # BnF UUID for XMP metadata box
        self.bnf_uuid = "BE7ACFCB97A942E89C71999491E3AFAC"
        self.base_handler = base_handler
        
        logger.info("Initialized BnFMetadataHandler")
        
        # Optional debug logging
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug(f"BnFMetadataHandler initialized with ExifTool: {base_handler.exiftool}")
    
    def write_bnf_metadata(
        self,
        jp2_file: str,
        metadata: Dict[str, Any],
        compression_mode: str = "supervised",
        num_resolutions: int = 10,
        progression_order: str = "RPCL",
        dcterms_isPartOf: Optional[str] = None,
        dcterms_provenance: str = "Bibliothèque nationale de France",
        dc_relation: Optional[str] = None,
        dc_source: Optional[str] = None
    ) -> bool:
        """
        Write metadata in BnF-compliant XMP format.
        
        Args:
            jp2_file: Path to JPEG2000 file
            metadata: Base metadata dictionary
            compression_mode: Compression mode
            num_resolutions: Number of resolution levels
            progression_order: Progression order
            dcterms_isPartOf: Identifier of document (NUM or IFN format)
            dcterms_provenance: Owner of document
            dc_relation: ARK identifier
            dc_source: Original call number
            
        Returns:
            bool: True if successful
            
        Raises:
            FileNotFoundError: If the JPEG2000 file doesn't exist
            ValueError: If essential metadata is missing
            RuntimeError: If exiftool operation fails
        """
        # Validate input file
        if not os.path.exists(jp2_file):
            logger.error(f"JPEG2000 file not found: {jp2_file}")
            raise FileNotFoundError(f"JPEG2000 file not found: {jp2_file}")
        
        # Verify metadata structure
        if not isinstance(metadata, dict):
            logger.error(f"Invalid metadata format: {type(metadata)}")
            raise ValueError(f"Metadata must be a dictionary, got {type(metadata)}")
        
        try:
            # Check if exiftool is available
            if not self.exiftool:
                raise RuntimeError("ExifTool not found. Cannot write BnF metadata.")
            
            # Create BnF compliant XMP
            xmp_data = self._create_bnf_xmp_metadata(
                metadata,
                dcterms_isPartOf,
                dcterms_provenance,
                dc_relation,
                dc_source,
                compression_mode,
                num_resolutions,
                progression_order
            )
            
            # Write XMP to a temporary file
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".xmp", mode="w", delete=False) as tmp:
                    tmp.write(xmp_data)
                    tmp_path = tmp.name
                
                # Use exiftool to embed the XMP in the JP2 file with BnF UUID
                cmd = [
                    self.exiftool,
                    "-XMP-xmpmeta:all=",  # Clear existing XMP
                    f"-XMP-xmpmeta<={tmp_path}",  # Add XMP from file
                    f"-XMP-xmpmeta:UUID={self.bnf_uuid}",  # Set BnF UUID
                    "-overwrite_original",
                    jp2_file
                ]
                
                try:
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,  # Get string output
                        check=False  # Handle exceptions manually for better error messages
                    )
                    
                    if result.returncode != 0:
                        error_msg = result.stderr.strip()
                        logger.error(f"ExifTool error: {error_msg}")
                        raise RuntimeError(f"ExifTool failed with error: {error_msg}")
                    
                    logger.info(f"Wrote BnF metadata to {jp2_file}")
                    return True
                    
                except subprocess.SubprocessError as e:
                    logger.error(f"Failed to execute ExifTool: {str(e)}")
                    raise RuntimeError(f"ExifTool execution failed: {str(e)}") from e
                    
            finally:
                # Clean up temporary file
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError as e:
                        logger.warning(f"Failed to remove temporary file {tmp_path}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error writing BnF metadata: {str(e)}")
            # Re-raise specific exceptions to be handled by caller
            if isinstance(e, (FileNotFoundError, ValueError, RuntimeError)):
                raise
            # For other exceptions, return False to maintain compatibility
            return False
    
    def _create_bnf_xmp_metadata(
        self,
        metadata: Dict[str, Any],
        dcterms_isPartOf: Optional[str] = None,
        dcterms_provenance: str = "Bibliothèque nationale de France",
        dc_relation: Optional[str] = None,
        dc_source: Optional[str] = None,
        compression_mode: str = "supervised",
        num_resolutions: int = 10,
        progression_order: str = "RPCL"
    ) -> str:
        """
        Create BnF compliant XMP metadata string.
        
        Args:
            metadata: Base metadata dictionary
            dcterms_isPartOf: Identifier (NUM or IFN format)
            dcterms_provenance: Owner of document
            dc_relation: ARK identifier
            dc_source: Original call number
            compression_mode: Compression mode
            num_resolutions: Number of resolution levels
            progression_order: Progression order
            
        Returns:
            str: XMP metadata string
            
        Raises:
            ValueError: If required metadata is missing
        """
        # Validate key metadata fields according to BnF requirements
        if not dcterms_isPartOf and not metadata.get("dcterms:isPartOf"):
            logger.warning("Missing required field dcterms:isPartOf for BnF compliance")
        
        # Extract creation date, modify date, and other needed values
        creation_date = metadata.get("xmp:CreateDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        modify_date = metadata.get("xmp:ModifyDate", datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"))
        creator_tool = metadata.get("xmp:CreatorTool", "JP2Forge")
        tiff_model = metadata.get("tiff:Model", "")
        tiff_make = metadata.get("tiff:Make", "")
        serial_number = metadata.get("aux:SerialNumber", "")
        tiff_artist = metadata.get("tiff:Artist", "")
        
        # BnF XMP template based on their reference
        # The Unicode character U+FEFF is required by BnF spec
        xml_template = f"""<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
 <rdf:Description 
 xmlns:xmp="http://ns.adobe.com/xap/1.0/" 
 xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
 xmlns:dc="http://purl.org/dc/elements/1.1/" 
 xmlns:dcterms="http://purl.org/dc/terms/" 
 xmlns:exif="http://ns.adobe.com/exif/1.0/" 
 xmlns:aux="http://ns.adobe.com/exif/1.0/aux/"
 rdf:about=""
 tiff:Model="{tiff_model}" 
 tiff:Make="{tiff_make}" 
 tiff:Artist="{tiff_artist}" 
 aux:SerialNumber="{serial_number}" 
 xmp:CreatorTool="{creator_tool}" 
 xmp:CreateDate="{creation_date}" 
 xmp:ModifyDate="{modify_date}">"""
        
        # Add dcterms:isPartOf if provided
        effective_isPartOf = dcterms_isPartOf or metadata.get("dcterms:isPartOf")
        if effective_isPartOf:
            xml_template += f"""
 <dcterms:isPartOf>
 <rdf:Bag>
 <rdf:li>{effective_isPartOf}</rdf:li>
 </rdf:Bag>
 </dcterms:isPartOf>"""
            
        # Add dcterms:provenance
        effective_provenance = dcterms_provenance or metadata.get("dcterms:provenance", "Bibliothèque nationale de France")
        xml_template += f"""
 <dcterms:provenance>
 <rdf:Bag>
 <rdf:li>{effective_provenance}</rdf:li>
 </rdf:Bag>
 </dcterms:provenance>"""
        
        # Add dc:relation if provided (ARK identifier)
        effective_relation = dc_relation or metadata.get("dc:relation")
        if effective_relation:
            xml_template += f"""
 <dc:relation>
 <rdf:Bag>
 <rdf:li>{effective_relation}</rdf:li>
 </rdf:Bag>
 </dc:relation>"""
            
        # Add dc:source if provided (original call number)
        effective_source = dc_source or metadata.get("dc:source")
        if effective_source:
            xml_template += f"""
 <dc:source>
 <rdf:Bag>
 <rdf:li>{effective_source}</rdf:li>
 </rdf:Bag>
 </dc:source>"""
        
        # Close the XML
        xml_template += """
 </rdf:Description>
</rdf:RDF>
</x:xmpmeta> 
<?xpacket end="r"?>"""

        return xml_template
    
    def create_bnf_compliant_metadata(
        self,
        identifiant: str,
        provenance: str = "Bibliothèque nationale de France",
        ark_identifiant: Optional[str] = None,
        cote: Optional[str] = None,
        scanner_model: Optional[str] = None,
        scanner_make: Optional[str] = None,
        serial_number: Optional[str] = None,
        creator_tool: str = "JP2Forge",
        operator: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create BnF-compliant metadata.
        
        Args:
            identifiant: Identifier in NUM_XXXXX or IFN_XXXXX format
            provenance: Document owner (default: BnF)
            ark_identifiant: ARK identifier
            cote: Original document call number
            scanner_model: Scanning equipment model
            scanner_make: Scanning equipment manufacturer
            serial_number: Scanning equipment serial number
            creator_tool: Software used for digitization
            operator: Digitization operator name
            
        Returns:
            dict: Dictionary with BnF metadata
            
        Raises:
            ValueError: If identifiant is not valid
        """
        # Validate identifiant format (should be NUM_ or IFN_ followed by digits)
        import re
        if not re.match(r'^(NUM|IFN)_\d+', identifiant):
            logger.warning(f"Identifier '{identifiant}' does not match BnF format (NUM_XXXXX or IFN_XXXXX)")
        
        metadata = {}
        
        # Required BnF fields
        metadata['dcterms:isPartOf'] = identifiant
        metadata['dcterms:provenance'] = provenance
        
        # Optional BnF fields
        if ark_identifiant:
            metadata['dc:relation'] = ark_identifiant
        if cote:
            metadata['dc:source'] = cote
            
        # Technical fields
        if scanner_model:
            metadata['tiff:Model'] = scanner_model
        if scanner_make:
            metadata['tiff:Make'] = scanner_make
        if serial_number:
            metadata['aux:SerialNumber'] = serial_number
        if creator_tool:
            metadata['xmp:CreatorTool'] = creator_tool
        if operator:
            metadata['tiff:Artist'] = operator
            
        # Add creation and modification dates
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        metadata['xmp:CreateDate'] = current_time
        metadata['xmp:ModifyDate'] = current_time
        
        return metadata
        
    def validate_bnf_compliance(self, jp2_file: str) -> Tuple[bool, List[str]]:
        """
        Validate if a JPEG2000 file is BnF compliant.
        
        Args:
            jp2_file: Path to JPEG2000 file
            
        Returns:
            tuple: (is_compliant, issues)
            
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        issues = []
        
        # Check if file exists
        if not os.path.exists(jp2_file):
            raise FileNotFoundError(f"File does not exist: {jp2_file}")
                
        try:
            # Check if file is a JPEG2000 file
            result = subprocess.run(
                [self.exiftool, "-FileType", jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                issues.append(f"ExifTool error: {result.stderr.strip()}")
                return False, issues
                
            if "JP2" not in result.stdout:
                issues.append("File is not a valid JPEG2000 file")
                return False, issues
                
            # Check for BnF UUID
            result = subprocess.run(
                [self.exiftool, "-XMP-xmpmeta:UUID", jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0 or self.bnf_uuid not in result.stdout:
                issues.append("XMP metadata does not have BnF UUID")
                
            # Check for required metadata fields
            result = subprocess.run(
                [self.exiftool, "-XMP:All", jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                issues.append(f"Failed to read XMP metadata: {result.stderr.strip()}")
            else:
                # Required BnF fields
                if "dcterms:isPartOf" not in result.stdout:
                    issues.append("Missing dcterms:isPartOf (identifier)")
                    
                if "dcterms:provenance" not in result.stdout:
                    issues.append("Missing dcterms:provenance (owner)")
                
            # Check JPEG2000 parameters
            result = subprocess.run(
                [self.exiftool, "-JPEG2000:All", jp2_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                issues.append(f"Failed to read JPEG2000 metadata: {result.stderr.strip()}")
            else:
                # Check for RPCL progression order
                if "RPCL" not in result.stdout:
                    issues.append("Progression order is not RPCL")
                    
                # Check resolution levels
                import re
                if "Resolution Levels" in result.stdout:
                    match = re.search(r"Resolution Levels\s*:\s*(\d+)", result.stdout)
                    if match:
                        levels = int(match.group(1))
                        if levels != 10:
                            issues.append(f"Number of resolution levels is {levels}, not 10")
            
            # Validate is successful if no issues found
            is_compliant = len(issues) == 0
            
            if is_compliant:
                logger.info(f"JPEG2000 file {jp2_file} is BnF compliant")
            else:
                logger.warning(f"JPEG2000 file {jp2_file} is not BnF compliant with {len(issues)} issues")
                for issue in issues:
                    logger.warning(f"- {issue}")
            
            return is_compliant, issues
            
        except Exception as e:
            logger.error(f"Error validating BnF compliance: {str(e)}")
            issues.append(f"Error validating: {str(e)}")
            return False, issues
