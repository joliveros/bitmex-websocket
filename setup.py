#!/usr/bin/env python

# -*- coding: utf-8 -*-

from setuptools import setup
from os.path import realpath


setup(name='bitmex_websocket',
      version='0.2.78',
      description='Bitmex websocket API',
      long_description=open('README.rst').read().strip(),
      author='José Oliveros',
      author_email='jose.oliveros.1983@gmail.com',
      url='https://github.com/joliveros/bitmex-websocket',
      packages=[
        'bitmex_websocket',
        'bitmex_websocket.auth'
      ],
      install_requires=['alog', 'pyee', 'requests', 'websocket-client', 'click'],
      include_package_data=True,
      tests_require=['flake8', 'mock', 'pytest', 'pytest-mock', 'pytest-cov'],
      license='MIT License',
      zip_safe=True,
      keywords='bitmex websocket bot cryptocurrency',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
      ])
