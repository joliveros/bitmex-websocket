#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup
from os.path import realpath


def get_version_info():
    version_file = open(realpath('./.version'))
    return version_file.read()


setup(name='bitmex_websocket',
      version=get_version_info(),
      description='Bitmex websocket API',
      long_description=open('README.rst').read().strip(),
      author='José Oliveros',
      author_email='jose.oliveros.1983@gmail.com',
      url='https://github.com/joliveros/bitmex-websocket',
      packages=['bitmex_websocket',
                'bitmex_websocket.auth'],
      include_package_data=True,
      license='MIT License',
      zip_safe=True,
      keywords='bitmex websocket bot cryptocurrency',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ])
