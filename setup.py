#!/usr/bin/env python

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

import sys,os

do_cython = False
try:
    from Cython.Build import cythonize
    do_cython = True
except ImportError:
    do_cython = False

if __name__ == "__main__":

    # The root of the siggen repo.
    basedir = os.path.dirname(os.path.abspath(__file__))


    # Set up the C++-extension.
    include_dirs = [
        "pygama",
        os.path.join(basedir, "c")
    ]

    try:
        import numpy as np
        include_dirs += [np.get_include(),]
    except ImportError:
        do_cython = False

    src = [os.path.join(basedir, "c", fn) for fn in [
        "siginspect.c",
    ]]
    ext = ".pyx" if do_cython else ".c"
    src += [
        os.path.join("pygama", "_pygama"+ext)
    ]

    ext = [Extension(
            "pygama._pygama",
            sources=src,
            language="c",
            include_dirs=include_dirs
        ),
        Extension(
                "pygama.transforms",
                sources=[os.path.join("pygama", "transforms"+ext)],
                language="c",
            )
        ]

    if do_cython: ext = cythonize(ext)

    setup(
        name="pygama",
        version="0.0.1",
        author="Ben Shanks",
        author_email="benjamin.shanks@gmail.com",
        packages=["pygama"],
        ext_modules=ext,
        install_requires=["numpy", "scipy", "pandas", "tables", "future"]
    )
