#!/usr/bin/env python3

from setuptools import setup

setup(
        name='jassbot-bp',
        version="1.0.0",
        packages=[
            'jassbot',
            'jassbot.templates.jassbot',
            'jassbot.static.jassbot',
            ],
        include_package_data=True,
        install_requires=[
            'flask',
            'markdown',
            'requests',
            ],
        )
