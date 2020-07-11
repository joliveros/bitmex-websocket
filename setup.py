#!/usr/bin/env python

# -*- coding: utf-8 -*-

from setuptools import setup
from pip._internal.req import parse_requirements
from os.path import realpath


def get_reqs_from_file(file):
    file_path = realpath(file)

    # parse_requirements() returns generator of pip.req.InstallRequirement
    # objects
    install_requirements = parse_requirements(file_path, session='nope')

    # reqs is a list of requirement
    # e.g. ['django==1.5.1', 'mezzanine==1.4.6']
    return [str(ir.req) for ir in install_requirements]


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
      packages=[
        'bitmex_websocket',
        'bitmex_websocket.auth'
      ],
      install_requires=get_reqs_from_file('./requirements.txt'),
      include_package_data=True,
      tests_require=get_reqs_from_file('./requirements-test.txt'),
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
