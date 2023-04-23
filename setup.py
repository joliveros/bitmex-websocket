#!/usr/bin/env python

from setuptools import setup
from os.path import realpath


def get_reqs_from_file(file):
    file_path = realpath(file)

    with open(file_path) as req_file_contents:
        install_requirements = req_file_contents.readlines()
        return [req.strip() for req in install_requirements]


setup(name='bitmex_websocket',
      version=open(realpath('./.version')).read(),
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
      zip_safe=True,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.11',
      ])
