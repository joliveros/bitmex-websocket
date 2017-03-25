import setuptools
from bitmex_websocket.version import Version

setuptools.setup(name='bitmex-websocket',
                 version=Version('0.1.1').number,
                 description='Bitmex websocket API',
                 long_description=open('README.rst').read().strip(),
                 author='José Oliveros',
                 author_email='jose.oliveros.1983@gmail.com',
                 url='https://github.com/joliveros/bitmex-websocket',
                 py_modules=['bitmex-websocket'],
                 install_requires=[
                     'future',
                     'pyee',
                     'websocket-client'
                 ],
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
