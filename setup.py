import setuptools
from bitmext_websocket.version import Version


setuptools.setup(name='bitmex-websocket',
                 version=Version('0.1.0').number,
                 description='Bitmex websocket API',
                 long_description=open('README.md').read().strip(),
                 author='José Oliveros,
                 author_email='chinnno15@gmail.com',
                 url='https://github.com/joliveros/bitmex-websocket',
                 py_modules=['bitmex-websocket'],
                 install_requires=[],
                 license='MIT License',
                 zip_safe=False,
                 keywords='bitmex websocket bot cryptocurrency',
                 classifiers=['Packages'])
