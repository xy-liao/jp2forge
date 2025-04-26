"""
XMP metadata manager using lxml for advanced XML processing.

This module provides tools for reading, writing, and manipulating
XMP metadata using the lxml library for proper XML handling.
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

# Import lxml for proper XML handling
from lxml import etree
from lxml.builder import ElementMaker

from utils.xml.namespace_registry import NamespaceRegistry

logger = logging.getLogger(__name__)

# UUID for BnF XMP metadata box
BNF_UUID = "BE7ACFCB97A942E89C71999491E3AFAC"


class XMPManager:
    """
    Manager for XMP metadata using lxml for proper XML handling.

    This class provides tools for creating, reading, and manipulating
    XMP metadata with proper namespace support and XML validation.
    """

    def __init__(self, namespace_registry: Optional[NamespaceRegistry] = None):
        """
        Initialize the XMP manager.

        Args:
            namespace_registry: Registry for XML namespaces, or None to create new
        """
        # Initialize namespace registry
        self.registry = namespace_registry or NamespaceRegistry()

        # Create namespace element makers for XML creation
        self._element_makers = self._create_element_makers()

        logger.debug("XMPManager initialized")

    def _create_element_makers(self) -> Dict[str, ElementMaker]:
        """
        Create element makers for XML namespaces.

        Returns:
            dict: ElementMaker instances for each namespace
        """
        element_makers = {}
        ns_map = self.registry.get_namespace_map()

        for prefix, uri in ns_map.items():
            element_makers[prefix] = ElementMaker(
                namespace=uri,
                nsmap={prefix: uri}
            )

        return element_makers

    def _add_list_item_to_bag(
        self,
        parent_element: etree.Element,
        value: str,
        rdf: ElementMaker
    ) -> None:
        """
        Add a value to an RDF Bag element.

        Args:
            parent_element: Parent element to add to
            value: Value to add
            rdf: RDF element maker
        """
        li = rdf.li(value)
        parent_element.append(li)

    def create_empty_xmp(self) -> etree.Element:
        """
        Create an empty XMP metadata structure.

        Returns:
            etree.Element: Root element of XMP metadata
        """
        # Get namespace element makers
        nsmap = self.registry.get_namespace_map()
        x = self._element_makers['x']
        rdf = self._element_makers['rdf']

        # Create XMP structure
        xmpmeta = x('xmpmeta', {'id': 'W5M0MpCehiHzreSzNTczkc9d'})
        rdf_element = rdf.RDF()
        xmpmeta.append(rdf_element)

        return xmpmeta

    def create_xmp_with_metadata(
        self,
        metadata: Dict[str, Any],
        include_packet_wrapper: bool = True
    ) -> str:
        """
        Create XMP metadata XML from a metadata dictionary.

        Args:
            metadata: Dictionary of metadata values
            include_packet_wrapper: Include XMP packet wrapper

        Returns:
            str: XMP metadata as XML string
        """
        # Create empty XMP structure
        xmpmeta = self.create_empty_xmp()
        rdf_element = xmpmeta.find('.//{' + self.registry.get_uri('rdf') + '}RDF')

        # Get namespace element makers
        rdf_maker = self._element_makers['rdf']

        # Create description element
        description = rdf_maker.Description({'{' + self.registry.get_uri('rdf') + '}about': ''})
        rdf_element.append(description)

        # Add metadata properties
        for key, value in metadata.items():
            # Parse the namespace prefix and property name
            if ':' in key:
                prefix, name = key.split(':', 1)
                ns_uri = self.registry.get_uri(prefix)

                if not ns_uri:
                    logger.warning(f"Unknown namespace prefix: {prefix}")
                    continue

                # Create property element based on value type
                if isinstance(value, list):
                    # Create a Bag for lists
                    bag_parent = etree.Element('{' + ns_uri + '}' + name)
                    bag = rdf_maker.Bag()
                    bag_parent.append(bag)

                    for item in value:
                        self._add_list_item_to_bag(bag, str(item), rdf_maker)

                    description.append(bag_parent)

                else:
                    # Add simple property
                    prop_element = etree.Element('{' + ns_uri + '}' + name)
                    prop_element.text = str(value)
                    description.append(prop_element)
            else:
                logger.warning(f"Skipping metadata property without namespace prefix: {key}")

        # Convert to string
        xmp_xml = etree.tostring(
            xmpmeta,
            encoding='utf-8',
            xml_declaration=True,
            pretty_print=True
        ).decode('utf-8')

        # Add XMP packet wrapper if requested
        if include_packet_wrapper:
            xmp_xml = (
                '<?xpacket begin="\\xEF\\xBB\\xBF" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
                + xmp_xml +
                '\n<?xpacket end="r"?>'
            )

        return xmp_xml

    def create_bnf_metadata(
        self,
        document_id: str,
        source: str,
        ark_identifier: str,
        provenance: str = "Bibliothèque nationale de France",
        device_make: Optional[str] = None,
        device_model: Optional[str] = None,
        device_serial: Optional[str] = None,
        creator_tool: Optional[str] = None,
        artist: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a metadata dictionary for BnF-compliant metadata.

        Args:
            document_id: Document identifier (NUM_* or IFN_*)
            source: Original document call number
            ark_identifier: ARK identifier
            provenance: Document owner
            device_make: Device manufacturer
            device_model: Device model
            device_serial: Device serial number
            creator_tool: Software used for creation
            artist: Digitization operator or organization
            additional_metadata: Additional metadata to include

        Returns:
            dict: Metadata dictionary
        """
        # Format dates according to ISO-8601
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Create base BnF metadata
        metadata = {
            # Dublin Core - Required by BnF
            'dcterms:isPartOf': [document_id],
            'dcterms:provenance': [provenance],
            'dc:relation': [ark_identifier],
            'dc:source': [source],

            # Technical - Required by BnF if available
            'xmp:CreateDate': now,
            'xmp:ModifyDate': now
        }

        # Add optional technical metadata if provided
        if device_make:
            metadata['tiff:Make'] = device_make

        if device_model:
            metadata['tiff:Model'] = device_model

        if device_serial:
            metadata['aux:SerialNumber'] = device_serial

        if creator_tool:
            metadata['xmp:CreatorTool'] = creator_tool

        if artist:
            metadata['tiff:Artist'] = artist

        # Add additional metadata if provided
        if additional_metadata:
            for key, value in additional_metadata.items():
                if key not in metadata:  # Don't override standard fields
                    metadata[key] = value

        return metadata

    def create_bnf_uuid_box(self, metadata: Dict[str, Any]) -> bytes:
        """
        Create a BnF-compliant UUID box for XMP metadata.

        Args:
            metadata: Metadata dictionary

        Returns:
            bytes: UUID box content
        """
        # Create XMP XML
        xmp_xml = self.create_xmp_with_metadata(metadata)

        # Return as bytes
        return xmp_xml.encode('utf-8')

    def parse_xmp_string(self, xmp_string: str) -> Dict[str, Any]:
        """
        Parse XMP metadata from an XML string.

        Args:
            xmp_string: XMP metadata as XML string

        Returns:
            dict: Parsed metadata
        """
        try:
            # Parse XML
            parser = etree.XMLParser(remove_blank_text=True)
            root = etree.fromstring(xmp_string.encode('utf-8'), parser)

            # Find RDF element
            rdf_uri = self.registry.get_uri('rdf')
            rdf_element = root.find('.//{' + rdf_uri + '}RDF')

            if rdf_element is None:
                logger.warning("No RDF element found in XMP metadata")
                return {}

            # Find Description element
            desc_element = rdf_element.find('.//{' + rdf_uri + '}Description')

            if desc_element is None:
                logger.warning("No Description element found in XMP metadata")
                return {}

            # Extract metadata
            metadata = {}

            # Process child elements
            for element in desc_element:
                # Get namespace URI and local name
                if element.tag.startswith('{'):
                    ns_uri = element.tag.split('}')[0][1:]
                    local_name = element.tag.split('}')[1]

                    # Find prefix for namespace
                    prefix = self.registry.get_prefix_for_uri(ns_uri)

                    if prefix:
                        key = f"{prefix}:{local_name}"

                        # Check for Bag or Seq elements
                        bag = element.find('.//{' + rdf_uri + '}Bag')
                        seq = element.find('.//{' + rdf_uri + '}Seq')

                        if bag is not None or seq is not None:
                            container = bag if bag is not None else seq
                            items = container.findall('.//{' + rdf_uri + '}li')
                            values = [item.text for item in items if item.text]
                            metadata[key] = values
                        else:
                            # Simple value
                            metadata[key] = element.text if element.text else ""

            return metadata

        except Exception as e:
            logger.error(f"Error parsing XMP string: {e}")
            logger.debug(f"XMP string: {xmp_string[:200]}...")
            return {}

    def extract_xmp_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extract XMP metadata from a file using ExifTool.

        Args:
            file_path: Path to file

        Returns:
            dict: Extracted metadata
        """
        try:
            import subprocess

            # Run exiftool to extract XMP
            cmd = ['exiftool', '-xmp', '-b', file_path]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                check=False
            )

            if result.returncode != 0:
                logger.warning(f"ExifTool error: {result.stderr}")
                return {}

            # Parse the XMP data
            if result.stdout:
                return self.parse_xmp_string(result.stdout)
            else:
                logger.warning("No XMP data found")
                return {}

        except Exception as e:
            logger.error(f"Error extracting XMP from file: {e}")
            return {}

    def validate_bnf_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate metadata against BnF requirements.

        Args:
            metadata: Metadata dictionary

        Returns:
            tuple: (is_valid, issues)
        """
        issues = []

        # Required fields according to BnF
        required_fields = [
            'dcterms:isPartOf',
            'dcterms:provenance',
            'dc:relation',
            'dc:source'
        ]

        # Check required fields
        for field in required_fields:
            if field not in metadata:
                issues.append(f"Missing required field: {field}")
                continue

            # Check for empty values
            if isinstance(metadata[field], list):
                if not metadata[field]:
                    issues.append(f"Empty list for required field: {field}")
            elif not metadata[field]:
                issues.append(f"Empty value for required field: {field}")

        # Check isPartOf format (NUM_* or IFN_*)
        if 'dcterms:isPartOf' in metadata:
            value = metadata['dcterms:isPartOf']
            if isinstance(value, list):
                value = value[0] if value else ""

            if not (value.startswith("NUM_") or value.startswith("IFN_")):
                issues.append(
                    f"Invalid document ID format: {value} "
                    f"(should start with NUM_ or IFN_)"
                )

        # Check ARK identifier format
        if 'dc:relation' in metadata:
            value = metadata['dc:relation']
            if isinstance(value, list):
                value = value[0] if value else ""

            if not value.startswith("ark:"):
                issues.append(
                    f"Invalid ARK identifier format: {value} "
                    f"(should start with ark:)"
                )

        # Recommended technical fields
        recommended_fields = [
            'tiff:Make',
            'tiff:Model',
            'xmp:CreatorTool',
            'xmp:CreateDate',
            'xmp:ModifyDate'
        ]

        for field in recommended_fields:
            if field not in metadata:
                issues.append(f"Missing recommended field: {field}")

        # All validation checks passed if no issues found
        is_valid = len(issues) == 0

        if is_valid:
            logger.info("BnF metadata validation passed")
        else:
            logger.warning(f"BnF metadata validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"- {issue}")

        return is_valid, issues
