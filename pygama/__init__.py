# -*- coding: utf-8 -*-

__version__ = "0.0.1"

#kill annoying h5py warning
import warnings
warnings.filterwarnings(action="ignore", module="h5py", category=FutureWarning)
