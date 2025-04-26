"""
Metadata handler for JPEG2000 images.

This package provides functionality for managing metadata in
JPEG2000 images, including reading, writing, and validation.
"""

from core.metadata.base_handler import MetadataHandler
from core.metadata.bnf_handler import BnFMetadataHandler
from core.metadata.xmp_utils import create_standard_metadata

# Factory function to get the appropriate metadata handler


def get_metadata_handler(bnf_compliant: bool = False):
    """Factory function to get the appropriate metadata handler.

    Args:
        bnf_compliant: Whether to return a BnF-compliant handler

    Returns:
        MetadataHandler instance
    """
    if bnf_compliant:
        return BnFMetadataHandler()
    else:
        return MetadataHandler()


__all__ = ['MetadataHandler', 'BnFMetadataHandler',
           'create_standard_metadata', 'get_metadata_handler']
