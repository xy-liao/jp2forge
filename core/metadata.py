"""
Metadata handler for JPEG2000 images.

This module provides backward compatibility with the original monolithic 
metadata implementation by importing and reexporting the refactored classes.
"""

# Import from the refactored modules to maintain backward compatibility
from core.metadata.base_handler import MetadataHandler
from core.metadata.bnf_handler import BnFMetadataHandler
from core.metadata.xmp_utils import create_standard_metadata


# For backward compatibility, we'll provide a factory function that returns
# the appropriate handler based on whether BnF compliance is needed
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
