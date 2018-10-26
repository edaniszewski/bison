# -*- coding: utf-8 -*-
"""
bison
~~~~~

A Python application configuration library.
"""
# flake8: noqa

from .__version__ import (__author__, __author_email__, __copyright__,
                          __description__, __license__, __title__, __url__,
                          __version__)
from .bison import Bison
from .scheme import DictOption, ListOption, Option, Scheme
from .utils import DotDict
