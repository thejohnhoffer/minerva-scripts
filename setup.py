#!/usr/bin/env python
from setuptools import find_packages
from setuptools import setup

VERSION = 0.0
INSTALL_REQ = [
    'pypng>=0.0.18',
    'numpy>=1.14.3',
    'boto3>=1.7.81',
    'botocore>=1.10.81'
]

setup(
    version=VERSION,
    name='minerva-scripts',
    author='John Hoffer',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    author_email='john_hoffer@hms.harvard.edu',
    url="https://github.com/thejohnhoffer/minerva-scripts",
    description="Serve data from Minerva to Omero figure",
    install_requires=INSTALL_REQ
)
