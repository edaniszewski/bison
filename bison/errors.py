# -*- coding: utf-8 -*-
"""
bison.errors
~~~~~~~~~~~

This module defines the errors used by `bison`.
"""


class BisonError(Exception):
    """The base class for all `bison` errors."""


class InvalidSchemeError(BisonError):
    """Error for when a `Scheme` contains incorrect members."""


class SchemeValidationError(BisonError):
    """An error for when a `bison` scheme fails validation."""
