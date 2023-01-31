# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "requirements.txt")) as f:
    install_requires = f.read().strip().split("\n")

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="shuler_lab_to_nwb",
    version="0.1.0",
    description="NWB conversion scripts, functions, and classes for Shuler lab.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Luiz Tauffer and Ben Dichter.",
    email="ben.dichter@catalystneuro.com",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=install_requires,
)
