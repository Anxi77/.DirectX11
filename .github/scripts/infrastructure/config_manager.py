"""Enhanced configuration management with environment variable support."""
import os
import re
import logging
import yaml
from typing import Dict, Any, Optional, Union


class ConfigurationManager:
    """Manages configuration loading with environment variable substitution and validation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[Dict[str, Any]] = None
        self._required_fields = {
            'global.timezone': str,
            'github.max_retries': int,
            'logging.level': str,
        }
        self._env_substitution_pattern = re.compile(r'\$\{([^}]+)\}')

    def _find_config_file(self) -> str:
        """Find configuration file in standard locations.

        Returns:
            Path to configuration file
        """
        possible_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'config.yaml'),
            os.path.join(os.path.dirname(__file__), '..', 'config.yml'),
            'config.yaml',
            'config.yml'
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        raise FileNotFoundError("No configuration file found")

    def load_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Load and process configuration.

        Args:
            environment: Environment name for overrides (development, staging, production)

        Returns:
            Processed configuration dictionary
        """
        if self._config:
            return self._apply_environment_overrides(self._config.copy(), environment)

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)

            # Process environment variable substitutions
            processed_config = self._process_env_substitutions(raw_config)

            # Apply defaults for missing values
            processed_config = self._apply_defaults(processed_config)

            # Validate configuration
            self._validate_config(processed_config)

            # Apply environment overrides
            final_config = self._apply_environment_overrides(processed_config, environment)

            self._config = processed_config
            self.logger.info(f"Configuration loaded from {self.config_path}")

            return final_config

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _process_env_substitutions(self, config: Any) -> Any:
        """Process environment variable substitutions in configuration.

        Args:
            config: Configuration data (can be dict, list, or str)

        Returns:
            Configuration with environment variables substituted
        """
        if isinstance(config, dict):
            return {k: self._process_env_substitutions(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._process_env_substitutions(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_env_vars(config)
        else:
            return config

    def _substitute_env_vars(self, value: str) -> Union[str, int, bool]:
        """Substitute environment variables in a string value.

        Args:
            value: String that may contain environment variable references

        Returns:
            Value with environment variables substituted
        """
        def replace_env_var(match):
            env_expr = match.group(1)

            # Support default values: ${VAR:default}
            if ':' in env_expr:
                var_name, default_value = env_expr.split(':', 1)
                env_value = os.environ.get(var_name.strip(), default_value.strip())
            else:
                env_value = os.environ.get(env_expr.strip())
                if env_value is None:
                    self.logger.warning(f"Environment variable {env_expr} not found")
                    return match.group(0)  # Return original if not found

            return env_value

        result = self._env_substitution_pattern.sub(replace_env_var, value)

        # Try to convert to appropriate type
        return self._convert_value_type(result)

    def _convert_value_type(self, value: str) -> Union[str, int, bool]:
        """Convert string value to appropriate type.

        Args:
            value: String value to convert

        Returns:
            Value converted to appropriate type
        """
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Integer conversion
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)

        # Float conversion
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass

        return value

    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing configuration options.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with defaults applied
        """
        defaults = {
            'global': {
                'timezone': os.environ.get('TZ', 'UTC'),
                'project_number': int(os.environ.get('PROJECT_NUMBER', '1')),
                'max_retries': 3,
                'log_level': 'INFO'
            },
            'github': {
                'max_retries': 3,
                'base_delay': 1.0,
                'rate_limit_buffer': 100
            },
            'logging': {
                'level': os.environ.get('LOG_LEVEL', 'INFO'),
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            },
            'performance': {
                'batch_size': 50,
                'concurrent_requests': 5,
                'cache_duration': 300
            },
            'error_handling': {
                'max_errors_per_run': 10,
                'retry_failed_operations': True,
                'notification_on_critical_error': False
            }
        }

        return self._deep_merge(defaults, config)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _validate_config(self, config: Dict[str, Any]):
        """Validate configuration for required fields and types.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        errors = []

        for field_path, expected_type in self._required_fields.items():
            value = self._get_nested_value(config, field_path)
            if value is None:
                errors.append(f"Required field '{field_path}' is missing")
            elif not isinstance(value, expected_type):
                errors.append(f"Field '{field_path}' should be {expected_type.__name__}, got {type(value).__name__}")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path (e.g., 'global.timezone')

        Returns:
            Value at path or None if not found
        """
        keys = path.split('.')
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _apply_environment_overrides(self, config: Dict[str, Any], environment: Optional[str]) -> Dict[str, Any]:
        """Apply environment-specific configuration overrides.

        Args:
            config: Base configuration
            environment: Environment name

        Returns:
            Configuration with environment overrides applied
        """
        if not environment:
            environment = os.environ.get('AUTOMATION_ENV', 'development')

        environments = config.get('environments', {})
        env_overrides = environments.get(environment, {})

        if env_overrides:
            self.logger.info(f"Applying {environment} environment overrides")
            config = self._deep_merge(config, env_overrides)

        return config


def load_config(config_path: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to load configuration.

    Args:
        config_path: Path to configuration file
        environment: Environment name

    Returns:
        Loaded configuration
    """
    manager = ConfigurationManager(config_path)
    return manager.load_config(environment)
