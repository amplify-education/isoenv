#! /usr/bin/env python

from setuptools import setup

setup(
    name="isoenv",
    version="0.1",
    description=("Tools for keeping environment specific configuration "
                 "in a single repository, while only deploying the "
                 "configuration for a single environment"),
    author="Calen Pennington",
    author_email="cpennington@wgen.net",
    py_modules=["isoenv"],
    setup_requires=['nose'],
    install_requires=[
        'argparse',
        'nose',
    ],
    tests_require=['mock==0.6.0', 'decorator'],
    entry_points={
        'console_scripts': [
            'in_env = isoenv:in_env_main',
            'isoenv = isoenv:compile_main',
        ]
    }
)
