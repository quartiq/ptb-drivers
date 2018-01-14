#!/usr/bin/env python3

import sys
from setuptools import setup
from setuptools import find_packages


setup(
    name="ptb-drivers",
    version="0.1",
    description="Driver for PTB hardware used in opticlock (synthesizer, "
        "temperature measurement, amplifier, shutter driver, voltage source, "
        "current source)",
    long_description=open("README.rst").read(),
    author="Robert Jördens",
    author_email="rj@quartiq.de",
    url="https://github.com/quartiq/ptb-drivers",
    download_url="https://github.com/quartiq/ptb-drivers",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            # "aqctl_ptb_synth = ptb.aqctl_ptb_synth:main",
        ],
    },
    test_suite="ptb.test",
    license="LGPLv3+",
)
