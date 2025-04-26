"""
Configuration manager for JP2Forge.

This module provides tools for loading, validating, and managing
configuration from various sources.
"""

import os
import json
import logging
import yaml
from typing import Dict, Any, Optional, List, Tuple, Union

from utils.config.config_schema import ConfigSchema

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manager for JP2Forge configuration.
    
    This class provides methods for loading configuration from files,
    environment variables, and command-line arguments with a hierarchical
    override system.
    """
    
    def __init__(self, config_schema: Optional[ConfigSchema] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_schema: Schema for configuration validation
        """
        self.schema = config_schema or ConfigSchema()
        
        # Start with default configuration
        self.config = self.schema.get_default_config()
        
        # Track configuration sources for diagnostics
        self._sources = {
            'default': set(self._flatten_keys(self.config))
        }
        
        logger.debug("ConfigManager initialized with default configuration")
    
    def _flatten_keys(self, d: Dict[str, Any], prefix: str = '') -> List[str]:
        """
        Get a flattened list of keys from a nested dictionary.
        
        Args:
            d: Dictionary to flatten
            prefix: Prefix for nested keys
            
        Returns:
            list: Flattened keys
        """
        keys = []
        
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            
            if isinstance(v, dict):
                keys.extend(self._flatten_keys(v, key))
            else:
                keys.append(key)
        
        return keys
    
    def _get_nested(self, d: Dict[str, Any], path: str) -> Any:
        """
        Get a value from a nested dictionary using a dot-separated path.
        
        Args:
            d: Dictionary to search
            path: Dot-separated path
            
        Returns:
            any: Value at the path, or None if not found
        """
        parts = path.split('.')
        current = d
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _set_nested(self, d: Dict[str, Any], path: str, value: Any) -> None:
        """
        Set a value in a nested dictionary using a dot-separated path.
        
        Args:
            d: Dictionary to modify
            path: Dot-separated path
            value: Value to set
        """
        parts = path.split('.')
        current = d
        
        # Navigate to the parent of the target node
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value at the target node
        current[parts[-1]] = value
    
    def load_from_file(
        self,
        file_path: str,
        required: bool = False
    ) -> bool:
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to configuration file (JSON or YAML)
            required: Whether the file is required to exist
            
        Returns:
            bool: True if file was loaded successfully
        """
        if not os.path.exists(file_path):
            if required:
                raise FileNotFoundError(f"Configuration file not found: {file_path}")
            else:
                logger.warning(f"Configuration file not found: {file_path}")
                return False
        
        try:
            # Determine file format from extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.yml', '.yaml']:
                # Load YAML
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            elif ext in ['.json']:
                # Load JSON
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
            else:
                logger.warning(f"Unsupported configuration file format: {ext}")
                return False
            
            if not isinstance(config_data, dict):
                logger.warning(f"Invalid configuration format in {file_path}: not a dictionary")
                return False
            
            # Track configuration source
            source_name = os.path.basename(file_path)
            self._sources[source_name] = set()
            
            # Update configuration (nested merge)
            self._merge_config(config_data, source=source_name)
            
            logger.info(f"Loaded configuration from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            if required:
                raise
            return False
    
    def _merge_config(
        self,
        config_data: Dict[str, Any],
        prefix: str = '',
        source: str = 'unknown'
    ) -> None:
        """
        Merge configuration data into the current configuration.
        
        Args:
            config_data: Configuration data to merge
            prefix: Prefix for nested keys
            source: Source identifier for tracking
        """
        for key, value in config_data.items():
            path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recursively merge dictionaries
                self._merge_config(value, path, source)
            else:
                # Set leaf value
                self._set_nested(self.config, path, value)
                
                # Track source
                if source in self._sources:
                    self._sources[source].add(path)
    
    def load_from_env(
        self,
        prefix: str = 'JP2FORGE_'
    ) -> int:
        """
        Load configuration from environment variables.
        
        Environment variables should be in the format:
        PREFIX_SECTION_KEY=value
        
        For example:
        JP2FORGE_GENERAL_VERBOSE=true
        
        Args:
            prefix: Prefix for environment variables
            
        Returns:
            int: Number of variables loaded
        """
        count = 0
        
        # Track configuration source
        self._sources['environment'] = set()
        
        # Find all environment variables with the prefix
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert key to configuration path
                # PREFIX_SECTION_KEY -> section.key
                config_path = key[len(prefix):].lower().replace('_', '.')
                
                # Convert value to appropriate type
                typed_value = self._convert_string_value(value)
                
                # Set in configuration
                self._set_nested(self.config, config_path, typed_value)
                
                # Track source
                self._sources['environment'].add(config_path)
                
                count += 1
                logger.debug(f"Loaded configuration from environment: {key}={typed_value}")
        
        if count > 0:
            logger.info(f"Loaded {count} configuration values from environment variables")
        
        return count
    
    def _convert_string_value(self, value: str) -> Any:
        """
        Convert string value to appropriate type.
        
        Args:
            value: String value to convert
            
        Returns:
            any: Converted value
        """
        # Convert boolean values
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        # Convert numeric values
        try:
            # Try integer first
            return int(value)
        except ValueError:
            try:
                # Then try float
                return float(value)
            except ValueError:
                # Keep as string if not numeric
                return value
    
    def update_from_dict(
        self,
        config_data: Dict[str, Any],
        source: str = 'runtime'
    ) -> None:
        """
        Update configuration from a dictionary.
        
        Args:
            config_data: Configuration dictionary
            source: Source identifier for tracking
        """
        # Track configuration source
        self._sources[source] = set()
        
        # Update configuration
        self._merge_config(config_data, source=source)
        
        logger.debug(f"Updated configuration from {source}")
    
    def update_from_args(
        self,
        args: Dict[str, Any],
        mapping: Optional[Dict[str, str]] = None
    ) -> int:
        """
        Update configuration from command-line arguments.
        
        Args:
            args: Parsed command-line arguments
            mapping: Optional mapping from argument names to config paths
            
        Returns:
            int: Number of values updated
        """
        count = 0
        
        # Default mapping if not provided
        if mapping is None:
            mapping = {
                'verbose': 'general.verbose',
                'log_file': 'general.log_file',
                'log_level': 'general.log_level',
                'parallel': 'processing.mode',  # True -> 'parallel', False -> 'sequential'
                'max_workers': 'processing.max_workers',
                'memory_limit': 'processing.memory_limit_mb',
                'document_type': 'document_type',  # Special handling
                'compression_mode': 'jpeg2000.compression_mode',
                'bnf_compliant': 'bnf.compliant',
                'use_kakadu': 'bnf.use_kakadu',
                'kakadu_path': 'bnf.kakadu_path',
                'num_resolutions': 'jpeg2000.num_resolutions',
                'progression_order': 'jpeg2000.progression_order',
                'lossless_fallback': 'jpeg2000.lossless_fallback',
                'compression_ratio_tolerance': 'jpeg2000.compression_ratio_tolerance',
                'quality_threshold': 'quality_threshold',  # Special handling
                'preserve_icc_profiles': 'color.preserve_icc_profiles',
                'overwrite_existing': 'output.overwrite_existing',
                'create_report': 'output.create_report',
            }
        
        # Track configuration source
        self._sources['args'] = set()
        
        # Update configuration from arguments
        for arg_name, config_path in mapping.items():
            if arg_name in args and args[arg_name] is not None:
                value = args[arg_name]
                
                # Special handling for some arguments
                if arg_name == 'parallel':
                    value = 'parallel' if value else 'sequential'
                elif arg_name == 'document_type':
                    # Don't set this directly - quality threshold is tied to document type
                    # Just capture the document type to use with quality_threshold
                    document_type = value
                    continue
                elif arg_name == 'quality_threshold':
                    # Set quality threshold for the selected document type
                    if 'document_type' in args and args['document_type']:
                        doc_type = args['document_type']
                        config_path = f'document_types.{doc_type}.quality_threshold'
                    else:
                        # Use photograph as default
                        config_path = 'document_types.photograph.quality_threshold'
                
                # Set in configuration
                self._set_nested(self.config, config_path, value)
                
                # Track source
                self._sources['args'].add(config_path)
                
                count += 1
                logger.debug(f"Updated configuration from args: {arg_name}={value}")
        
        if count > 0:
            logger.info(f"Updated {count} configuration values from command-line arguments")
        
        return count
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the current configuration.
        
        Returns:
            tuple: (is_valid, issues)
        """
        return self.schema.validate_config(self.config)
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a value from the configuration.
        
        Args:
            path: Dot-separated path
            default: Default value if not found
            
        Returns:
            any: Value from configuration or default
        """
        value = self._get_nested(self.config, path)
        return default if value is None else value
    
    def set(self, path: str, value: Any, source: str = 'runtime') -> None:
        """
        Set a value in the configuration.
        
        Args:
            path: Dot-separated path
            value: Value to set
            source: Source identifier for tracking
        """
        self._set_nested(self.config, path, value)
        
        # Track source
        if source not in self._sources:
            self._sources[source] = set()
        self._sources[source].add(path)
        
        logger.debug(f"Set configuration: {path}={value} (source: {source})")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration.
        
        Returns:
            dict: Configuration dictionary
        """
        return self.config.copy()
    
    def save_to_file(self, file_path: str, format: str = 'auto') -> bool:
        """
        Save the current configuration to a file.
        
        Args:
            file_path: Path to save configuration
            format: File format ('json', 'yaml', or 'auto')
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Determine format
            if format == 'auto':
                ext = os.path.splitext(file_path)[1].lower()
                format = 'yaml' if ext in ['.yml', '.yaml'] else 'json'
            
            # Create directory if needed
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save in requested format
            if format == 'yaml':
                with open(file_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            else:  # json
                with open(file_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            logger.info(f"Saved configuration to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {e}")
            return False
    
    def get_source_info(self) -> Dict[str, int]:
        """
        Get information about configuration sources.
        
        Returns:
            dict: Source information (source -> count)
        """
        return {source: len(keys) for source, keys in self._sources.items()}
    
    def get_value_source(self, path: str) -> Optional[str]:
        """
        Get the source of a configuration value.
        
        Args:
            path: Dot-separated path
            
        Returns:
            str: Source identifier or None if not found
        """
        # Check all sources in reverse priority order
        for source in reversed(list(self._sources.keys())):
            if path in self._sources[source]:
                return source
        
        return None
