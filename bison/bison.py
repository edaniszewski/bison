# -*- coding: utf-8 -*-
"""
bison.bison
~~~~~~~~~~~

This module implements the `bison` API.
"""

import logging
import os

import yaml

from bison.errors import BisonError
from bison.utils import DotDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# enumerate the supported configuration formats
YAML, = range(1)


class Bison(object):
    """The configuration management object.

    The `Bison` object is used to search for, read, parse, and validate
    application configurations based on a set of defaults, configuration
    files, environment variables, and overrides. `Bison` is not intended
    to incorporate command line arguments.

    By default, `Bison` is configured to look for a file named 'config'
    with the YAML format (file extension .yml or .yaml).

    Args:
        scheme (bison.Scheme): The scheme to use for validation when parsing
            a configuration file. If no scheme is provided, no validation will
            occur. (default: None)
        enable_logging (bool): Enable `bison` logging. If this is set to True,
            `bison` will log out at the logging.INFO level; otherwise, logging
            for `bison` is disabled. (default: False)
    """

    # map the configuration format to its supported file extensions
    _fmt_to_ext = {
        YAML: ('.yml', '.yaml')
    }

    # map the configuration format to the function is uses to load
    # the configuration data from file.
    _fmt_to_parser = {
        YAML: yaml.safe_load
    }

    def __init__(self, scheme=None, enable_logging=False):
        logger.disabled = not enable_logging

        self.scheme = scheme

        self.config_name = 'config'  # the name of the config file
        self.config_format = YAML  # format of the config file
        self.config_paths = []  # the path(s) to search for the config file
        self.config_file = None  # the config file to read

        self.env_prefix = None  # the environment variable prefix
        self.auto_env = False  # automatically bind options to env variables

        # the component configurations
        self._default = DotDict()
        self._config = DotDict()
        self._environment = DotDict()
        self._override = DotDict()

        # the unified configuration.
        self._full_config = None

    @property
    def config(self):
        """Get the complete configuration where the default, config,
        environment, and override values are merged together.

        Returns:
            (DotDict): A dictionary of configuration values that
                allows lookups using dot notation.
        """
        if self._full_config is None:
            self._full_config = DotDict()
            self._full_config.merge(self._default)
            self._full_config.merge(self._config)
            self._full_config.merge(self._environment)
            self._full_config.merge(self._override)
        return self._full_config

    def get(self, key, default=None):
        """Get the value for the configuration `key`.

        Args:
            key (str): The key into the configuration dictionary to get.
            default: The value to return if the given `key` is not found
                in the `Bison` config. This defaults to `None`.

        Returns:
            The value for the given key, if it exists; `None` otherwise.
        """
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a value in the `Bison` configuration.

        Args:
            key (str): The configuration key to set a new value for.
            value: The value to set.
        """
        # the configuration changes, so we invalidate the cached config
        self._full_config = None
        self._override[key] = value

    def add_config_paths(self, *paths):
        """Add paths to search for the configuration file.

        Args:
            *paths (str): The paths to search in for the configuration file.
        """
        self.config_paths.extend(paths)

    def validate(self):
        """Validate the `Bison` configuration against the `Scheme`, if one
        is set.

        Raises:
            errors.SchemeValidationError: The `Bison` configuration fails
                schema validation.
        """
        if self.scheme:
            self.scheme.validate(self.config)

    def parse(self, requires_cfg=True):
        """Parse the configuration sources into `Bison`.

        Args:
            requires_cfg (bool): Specify whether or not parsing should fail
                if a config file is not found. (default: True)
        """
        self._parse_default()
        self._parse_config(requires_cfg)
        self._parse_env()

    def _find_config(self):
        """Searches through the configured `config_paths` for the `config_name`
        file.

        If there are no `config_paths` defined, this will raise an error, so the
        caller should take care to check the value of `config_paths` first.

        Returns:
            str: The fully qualified path to the configuration that was found.

        Raises:
            Exception: No paths are defined in `config_paths` or no file with
                the `config_name` was found in any of the specified `config_paths`.
        """
        for search_path in self.config_paths:
            for ext in self._fmt_to_ext.get(self.config_format):
                path = os.path.abspath(os.path.join(search_path, self.config_name + ext))
                if os.path.isfile(path):
                    self.config_file = path
                    return
        raise BisonError('No file named {} found in search paths {}'.format(
            self.config_name, self.config_paths))

    def _parse_config(self, requires_cfg=True):
        """Parse the configuration file, if one is configured, and add it to
        the `Bison` state.

        Args:
            requires_cfg (bool): Specify whether or not parsing should fail
                if a config file is not found. (default: True)
        """
        if len(self.config_paths) > 0:
            try:
                self._find_config()
            except BisonError:
                if not requires_cfg:
                    return
                raise
            try:
                with open(self.config_file, 'r') as f:
                    parsed = self._fmt_to_parser[self.config_format](f)
            except Exception as e:
                raise BisonError(
                    'Failed to parse config file: {}'.format(self.config_file)
                ) from e

            # the configuration changes, so we invalidate the cached config
            self._full_config = None
            self._config = parsed

    def _parse_env(self):
        """Parse the environment variables for any configuration if an `env_prefix`
        is set.
        """
        env_cfg = DotDict()

        # if the env prefix doesn't end with '_', we'll append it here
        if self.env_prefix and not self.env_prefix.endswith('_'):
            self.env_prefix = self.env_prefix + '_'

        # if there is no scheme, we won't know what to look for so only parse
        # config if there is a scheme.
        if self.scheme:
            for k, v in self.scheme.flatten().items():
                value = v.parse_env(k, self.env_prefix, self.auto_env)
                if value is not None:
                    env_cfg[k] = value

        if len(env_cfg) > 0:
            # the configuration changes, so we invalidate the cached config
            self._full_config = None
            self._environment.update(env_cfg)

    def _parse_default(self):
        """Parse the `Schema` for the `Bison` instance to create the set of
        default values.

        If no defaults are specified in the `Schema`, the default dictionary
        will not contain anything.
        """
        # the configuration changes, so we invalidate the cached config
        self._full_config = None

        if self.scheme:
            self._default.update(self.scheme.build_defaults())
