# -*- coding: utf-8 -*-

__version__ = "0.0.1"

try:
    __PYGAMA_SETUP__
except NameError:
    __PYGAMA_SETUP__ = False

if not __PYGAMA_SETUP__:
    # __all__ = [._siggen import]

    from ._pygama import ProcessTier0,ProcessTier1, TierOneProcessorList
    from .transforms import *
