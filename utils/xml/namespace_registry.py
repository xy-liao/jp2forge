"""
Namespace registry for XML and XMP processing.

This module provides a registry for XML namespaces used in XMP metadata.
"""

import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


class NamespaceRegistry:
    """
    Registry for XML namespaces used in XMP metadata.

    This class maintains standard namespaces and provides utilities
    for namespace handling.
    """

    # Standard XML namespaces used in XMP
    _STANDARD_NAMESPACES = {
        # Core namespaces
        'rdf': ('http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'rdf'),
        'xmp': ('http://ns.adobe.com/xap/1.0/', 'xmp'),
        'dc': ('http://purl.org/dc/elements/1.1/', 'dc'),
        'dcterms': ('http://purl.org/dc/terms/', 'dcterms'),
        'x': ('adobe:ns:meta/', 'x'),

        # Media namespaces
        'tiff': ('http://ns.adobe.com/tiff/1.0/', 'tiff'),
        'exif': ('http://ns.adobe.com/exif/1.0/', 'exif'),
        'aux': ('http://ns.adobe.com/exif/1.0/aux/', 'aux'),
        'iptc': ('http://ns.adobe.com/iptc/1.0/', 'iptc'),
        'photoshop': ('http://ns.adobe.com/photoshop/1.0/', 'photoshop'),
        'jpeg2000': ('http://ns.adobe.com/jpeg2000/1.0/', 'jpeg2000'),

        # Custom namespaces for BnF
        'bnf': ('http://bnf.fr/ns/jp2forge/1.0/', 'bnf')
    }

    def __init__(self):
        """Initialize the namespace registry with standard namespaces."""
        # Initialize with standard namespaces
        self._namespaces = self._STANDARD_NAMESPACES.copy()
        logger.debug(
            f"Initialized NamespaceRegistry with {len(self._namespaces)} standard namespaces")

    def register(self, prefix: str, uri: str, pref_prefix: Optional[str] = None) -> None:
        """
        Register a namespace in the registry.

        Args:
            prefix: Namespace prefix
            uri: Namespace URI
            pref_prefix: Preferred prefix for serialization (defaults to prefix)
        """
        self._namespaces[prefix] = (uri, pref_prefix or prefix)
        logger.debug(f"Registered namespace: {prefix} -> {uri}")

    def get_uri(self, prefix: str) -> Optional[str]:
        """
        Get the URI for a namespace prefix.

        Args:
            prefix: Namespace prefix

        Returns:
            str: Namespace URI or None if not found
        """
        if prefix in self._namespaces:
            return self._namespaces[prefix][0]
        return None

    def get_preferred_prefix(self, prefix: str) -> Optional[str]:
        """
        Get the preferred prefix for a namespace.

        Args:
            prefix: Namespace prefix

        Returns:
            str: Preferred prefix or None if not found
        """
        if prefix in self._namespaces:
            return self._namespaces[prefix][1]
        return None

    def get_prefix_for_uri(self, uri: str) -> Optional[str]:
        """
        Find the prefix for a namespace URI.

        Args:
            uri: Namespace URI

        Returns:
            str: Prefix or None if not found
        """
        for prefix, (namespace_uri, _) in self._namespaces.items():
            if namespace_uri == uri:
                return prefix
        return None

    def get_all_namespaces(self) -> Dict[str, Tuple[str, str]]:
        """
        Get all registered namespaces.

        Returns:
            dict: Dictionary of namespaces
        """
        return self._namespaces.copy()

    def get_namespace_map(self) -> Dict[str, str]:
        """
        Get namespace map for lxml.

        Returns:
            dict: Prefix -> URI mapping for lxml
        """
        return {prefix: uri for prefix, (uri, _) in self._namespaces.items()}

    def get_standard_prefixes(self) -> List[str]:
        """
        Get list of standard namespace prefixes.

        Returns:
            list: Standard prefixes
        """
        return list(self._STANDARD_NAMESPACES.keys())

    def is_standard_prefix(self, prefix: str) -> bool:
        """
        Check if a prefix is a standard namespace prefix.

        Args:
            prefix: Namespace prefix

        Returns:
            bool: True if standard, False otherwise
        """
        return prefix in self._STANDARD_NAMESPACES
