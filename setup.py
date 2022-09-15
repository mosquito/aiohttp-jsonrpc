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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=("tests",)),
    package_data={"aiohttp_jsonrpc": ["py.typed"]},
    install_requires=(
        "aiohttp",
        "typing-extensions; python_version<'3.8'"
    ),
    extras_require={
        "develop": [
            "pytest",
            "pytest-cov",
            "pytest-aiohttp",
        ],
    },
)
