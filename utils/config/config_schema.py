"""
Configuration schema definition for JP2Forge.

This module defines the schema for configuration validation
and provides default configuration values.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Set, Tuple

logger = logging.getLogger(__name__)

class ConfigSchema:
    """
    Configuration schema and default values for JP2Forge.
    
    This class defines the schema for configuration validation
    and provides default values for all settings.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # General settings
        'general': {
            'verbose': False,
            'log_file': None,
            'log_level': 'INFO',
        },
        
        # Processing settings
        'processing': {
            'mode': 'sequential',  # 'sequential' or 'parallel'
            'max_workers': 0,  # 0 = auto-detect (CPUs - 1)
            'min_workers': 1,
            'memory_limit_mb': 4096,
            'chunk_size': 1000000,  # Number of pixels per chunk
            'use_memory_mapping': True,
            'temp_dir': None,
            'force_chunking': False,
        },
        
        # Document types
        'document_types': {
            'photograph': {
                'compression_ratio': 4.0,
                'quality_threshold': 40.0,
            },
            'heritage_document': {
                'compression_ratio': 4.0,
                'quality_threshold': 45.0,
            },
            'color': {
                'compression_ratio': 6.0,
                'quality_threshold': 35.0,
            },
            'grayscale': {
                'compression_ratio': 16.0,
                'quality_threshold': 40.0,
            },
        },
        
        # JPEG2000 settings
        'jpeg2000': {
            'num_resolutions': 10,
            'progression_order': 'RPCL',
            'code_block_size': '64,64',
            'precinct_size': '256,256,256,256,128,128',
            'tile_size': '1024,1024',
            'include_markers': True,
            'compression_mode': 'supervised',  # 'lossless', 'lossy', 'supervised', 'bnf_compliant'
            'lossless_fallback': True,
            'compression_ratio_tolerance': 0.05,
        },
        
        # BnF settings
        'bnf': {
            'compliant': False,
            'use_kakadu': False,
            'kakadu_path': None,
            'uuid': 'BE7ACFCB97A942E89C71999491E3AFAC',
        },
        
        # Metadata settings
        'metadata': {
            'creator_tool': 'JP2Forge',
            'artist': None,
            'provenance': 'Bibliothèque nationale de France',
            'custom_fields': {},
        },
        
        # Tool settings
        'tools': {
            'exiftool_path': 'exiftool',
            'prefer_system_tools': True,
            'tool_timeout': 60,  # Seconds
        },
        
        # Color management
        'color': {
            'preserve_icc_profiles': True,
            'default_rgb_profile': None,
            'default_cmyk_profile': None,
            'default_gray_profile': None,
        },
        
        # Output settings
        'output': {
            'overwrite_existing': False,
            'create_report': True,
            'report_format': 'md',  # 'md', 'json', or 'csv'
        },
    }
    
    # Schema for config validation
    SCHEMA = {
        'general.verbose': {'type': bool},
        'general.log_file': {'type': (str, type(None))},
        'general.log_level': {'type': str, 'enum': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']},
        
        'processing.mode': {'type': str, 'enum': ['sequential', 'parallel']},
        'processing.max_workers': {'type': int, 'min': 0},
        'processing.min_workers': {'type': int, 'min': 1},
        'processing.memory_limit_mb': {'type': int, 'min': 256},
        'processing.chunk_size': {'type': int, 'min': 1000},
        'processing.use_memory_mapping': {'type': bool},
        'processing.temp_dir': {'type': (str, type(None))},
        'processing.force_chunking': {'type': bool},
        
        'document_types.*.compression_ratio': {'type': float, 'min': 1.0},
        'document_types.*.quality_threshold': {'type': float, 'min': 0.0},
        
        'jpeg2000.num_resolutions': {'type': int, 'min': 1, 'max': 32},
        'jpeg2000.progression_order': {'type': str, 'enum': ['LRCP', 'RLCP', 'RPCL', 'PCRL', 'CPRL']},
        'jpeg2000.code_block_size': {'type': str},
        'jpeg2000.precinct_size': {'type': str},
        'jpeg2000.tile_size': {'type': str},
        'jpeg2000.include_markers': {'type': bool},
        'jpeg2000.compression_mode': {
            'type': str, 
            'enum': ['lossless', 'lossy', 'supervised', 'bnf_compliant']
        },
        'jpeg2000.lossless_fallback': {'type': bool},
        'jpeg2000.compression_ratio_tolerance': {'type': float, 'min': 0.0, 'max': 1.0},
        
        'bnf.compliant': {'type': bool},
        'bnf.use_kakadu': {'type': bool},
        'bnf.kakadu_path': {'type': (str, type(None))},
        'bnf.uuid': {'type': str},
        
        'metadata.creator_tool': {'type': str},
        'metadata.artist': {'type': (str, type(None))},
        'metadata.provenance': {'type': str},
        'metadata.custom_fields': {'type': dict},
        
        'tools.exiftool_path': {'type': str},
        'tools.prefer_system_tools': {'type': bool},
        'tools.tool_timeout': {'type': int, 'min': 1},
        
        'color.preserve_icc_profiles': {'type': bool},
        'color.default_rgb_profile': {'type': (str, type(None))},
        'color.default_cmyk_profile': {'type': (str, type(None))},
        'color.default_gray_profile': {'type': (str, type(None))},
        
        'output.overwrite_existing': {'type': bool},
        'output.create_report': {'type': bool},
        'output.report_format': {'type': str, 'enum': ['md', 'json', 'csv']},
    }
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """
        Get the default configuration.
        
        Returns:
            dict: Default configuration
        """
        return cls.DEFAULT_CONFIG.copy()
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Get the configuration schema.
        
        Returns:
            dict: Configuration schema
        """
        return cls.SCHEMA.copy()
    
    @classmethod
    def validate_config(
        cls, 
        config: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a configuration against the schema.
        
        Args:
            config: Configuration to validate
            
        Returns:
            tuple: (is_valid, issues)
        """
        issues = []
        
        # Get schema for validation
        schema = cls.get_schema()
        
        # Validate each field in the configuration
        for path, value in cls.flatten_dict(config):
            # Check if field exists in schema
            if path in schema:
                field_schema = schema[path]
                
                # Check type
                if not isinstance(value, field_schema['type']):
                    issues.append(
                        f"Invalid type for {path}: expected {field_schema['type']}, "
                        f"got {type(value)}"
                    )
                    continue
                
                # Check enum (if specified)
                if 'enum' in field_schema and value not in field_schema['enum']:
                    issues.append(
                        f"Invalid value for {path}: {value} not in {field_schema['enum']}"
                    )
                
                # Check min/max (if applicable)
                if isinstance(value, (int, float)):
                    if 'min' in field_schema and value < field_schema['min']:
                        issues.append(
                            f"Value for {path} is too small: {value} < {field_schema['min']}"
                        )
                    
                    if 'max' in field_schema and value > field_schema['max']:
                        issues.append(
                            f"Value for {path} is too large: {value} > {field_schema['max']}"
                        )
            
            # Check wildcard fields
            else:
                # Look for wildcard schemas that match this field
                wildcard_match = False
                
                for schema_path, field_schema in schema.items():
                    if '*' in schema_path:
                        # Convert schema path to regex pattern
                        pattern_parts = schema_path.split('.')
                        path_parts = path.split('.')
                        
                        if len(pattern_parts) == len(path_parts):
                            match = True
                            
                            for i, (pattern_part, path_part) in enumerate(zip(pattern_parts, path_parts)):
                                if pattern_part != '*' and pattern_part != path_part:
                                    match = False
                                    break
                            
                            if match:
                                wildcard_match = True
                                
                                # Validate against the wildcard schema
                                if not isinstance(value, field_schema['type']):
                                    issues.append(
                                        f"Invalid type for {path}: expected {field_schema['type']}, "
                                        f"got {type(value)}"
                                    )
                                    continue
                                
                                # Check enum (if specified)
                                if 'enum' in field_schema and value not in field_schema['enum']:
                                    issues.append(
                                        f"Invalid value for {path}: {value} not in {field_schema['enum']}"
                                    )
                                
                                # Check min/max (if applicable)
                                if isinstance(value, (int, float)):
                                    if 'min' in field_schema and value < field_schema['min']:
                                        issues.append(
                                            f"Value for {path} is too small: {value} < {field_schema['min']}"
                                        )
                                    
                                    if 'max' in field_schema and value > field_schema['max']:
                                        issues.append(
                                            f"Value for {path} is too large: {value} > {field_schema['max']}"
                                        )
                                
                                break  # Stop after first match
                
                if not wildcard_match:
                    logger.debug(f"No schema found for config path: {path}")
        
        # All validation checks passed if no issues found
        is_valid = len(issues) == 0
        
        if is_valid:
            logger.debug("Configuration validation passed")
        else:
            logger.warning(f"Configuration validation failed with {len(issues)} issues")
            for issue in issues:
                logger.warning(f"- {issue}")
        
        return is_valid, issues
    
    @staticmethod
    def flatten_dict(
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '.'
    ) -> List[Tuple[str, Any]]:
        """
        Flatten a nested dictionary with dot notation.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key for nested dictionaries
            sep: Separator for keys
            
        Returns:
            list: List of (key, value) tuples
        """
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(ConfigSchema.flatten_dict(v, new_key, sep=sep))
            else:
                items.append((new_key, v))
        
        return items
