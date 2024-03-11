#!/usr/bin/env python3

from setuptools import setup

setup(
      name='jassbot-bp',
      packages=[
          'jassbot',
          'jassbot.templates.jassbot',
          'jassbot.static.jassbot',
      ],
      include_package_data=True,
      )
