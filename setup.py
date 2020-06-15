from __future__ import absolute_import, print_function

from setuptools import find_packages, setup

import aiohttp_jsonrpc as module


setup(
    name=module.__name__.replace("_", "-"),
    version=module.__version__,
    author=module.__author__,
    license=module.__license__,
    description=module.description,
    long_description=open("README.rst").read(),
    platforms="all",
    classifiers=[
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=("tests",)),
    install_requires=(
        "aiohttp",
    ),
    extras_require={
        "develop": [
            "pytest",
            "pytest-cov",
            "pytest-aiohttp",
        ],
    },
)
