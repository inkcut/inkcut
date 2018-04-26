"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2017

@author: jrm
"""
import re
import sys
from setuptools import setup, find_packages

#: Common requirements
install_requires = [
    'twisted',
    'enamlx>=0.4.1',
    'pyqtgraph',
    'qtconsole',  # now optional
    'pyserial>=3.4',
    'jsonpickle',
    'lxml',  # use sudo apt install libxml2-dev libxslt-dev

    #'PyQt5', # Let users install whatever Qt they want
    'qt-reactor',

    # Python 2:
    'faulthandler; python_version < \'3.0\'',
    'enaml<=0.10.3; python_version < \'3.0\'',

    # Python 3
    'enaml>=0.10; python_version > \'3.0\'',

    # Linux:
    'pycups; sys_platform == \'linux2\'',
    'pycups; sys_platform == \'linux\'',

    # Windows:
    'pywin32; sys_platform == \'win32\''
]

# Read version
with open('inkcut/__init__.py') as f:
    m = re.search(r'version = ["\'](.+)["\']', f.read(), re.MULTILINE)
    assert m is not None, 'Failed to read version'
    version = m.group(1)


setup(
    name='inkcut',
    packages=find_packages(),
    include_package_data=True,
    version=version,
    author="Inkcut team",
    author_email="frmdstryr@gmail.com",
    license='GPLv3',
    url='https://github.com/codelv/inkcut/',
    description="An application for controlling 2D plotters, cutters, "
                "engravers, and CNC machines.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': ['inkcut = inkcut.app:main'],
    },
    install_requires=install_requires,
    #extras_require={
    #    # IPython console plugin
    #    'console':  ["qtconsole"],
    #}

)
