"""
XMP metadata utilities for JP2Forge.

This module provides utility functions for creating and manipulating
XMP metadata for JPEG2000 images.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def create_standard_metadata(
    title: Optional[str] = None,
    creator: Optional[str] = None,
    description: Optional[str] = None,
    rights: Optional[str] = None,
    source: Optional[str] = None,
    software: str = "JP2Forge"
) -> Dict[str, Any]:
    """Create a standard metadata dictionary.

    Args:
        title: Title of the image
        creator: Creator of the image
        description: Description of the image
        rights: Rights statement
        source: Source of the image
        software: Software used to create the image

    Returns:
        dict: Dictionary containing standard metadata
    """
    metadata = {
        'dublin_core': {},
        'technical': {}
    }

    # Add Dublin Core metadata
    if title:
        metadata['dublin_core']['title'] = title
    if creator:
        metadata['dublin_core']['creator'] = creator
    if description:
        metadata['dublin_core']['description'] = description
    if rights:
        metadata['dublin_core']['rights'] = rights
    if source:
        metadata['dublin_core']['source'] = source

    # Add format
    metadata['dublin_core']['format'] = 'image/jp2'

    # Add date
    metadata['dublin_core']['date'] = datetime.now().strftime("%Y-%m-%d")

    # Add software
    metadata['technical']['software'] = software

    return metadata


def validate_xmp_namespace(namespace: str, value: str) -> bool:
    """Validate that a value is appropriate for its XMP namespace.

    Args:
        namespace: XMP namespace prefix (e.g., 'dc', 'xmp', 'tiff')
        value: Value to validate

    Returns:
        bool: True if the value is valid for the namespace
    """
    # Basic validation rules for common namespaces
    if namespace == 'dc' or namespace == 'dcterms':
        # Dublin Core values shouldn't be empty
        return bool(value and value.strip())

    elif namespace == 'xmp':
        # Most XMP values have specific formats
        if 'Date' in namespace:
            # Check if it's a valid ISO date format
            try:
                # Just check basic format, not full ISO compliance
                return bool(value and len(value) >= 10)
            except ValueError:
                return False
        return bool(value)

    elif namespace == 'tiff':
        # TIFF values typically shouldn't be empty
        return bool(value and value.strip())

    # Default: just ensure it's not empty
    return bool(value and value.strip())


def escape_xml_string(text: str) -> str:
    """Escape special characters in a string for XML.

    Args:
        text: String to escape

    Returns:
        str: Escaped string
    """
    if not text:
        return ""

    # Replace special XML characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')

    return text


def format_xmp_date(dt: datetime) -> str:
    """Format a datetime object as an XMP date string.

    Args:
        dt: Datetime object

    Returns:
        str: Formatted XMP date string
    """
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_xmp_namespaces() -> Dict[str, str]:
    """Get a dictionary of common XMP namespace prefixes and URIs.

    Returns:
        dict: Dictionary of namespace prefixes and URIs
    """
    return {
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/',
        'xmp': 'http://ns.adobe.com/xap/1.0/',
        'tiff': 'http://ns.adobe.com/tiff/1.0/',
        'exif': 'http://ns.adobe.com/exif/1.0/',
        'aux': 'http://ns.adobe.com/exif/1.0/aux/',
        'jpeg2000': 'http://ns.adobe.com/jp2/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    }
