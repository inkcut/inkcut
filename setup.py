"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2017

@author: jrm
"""
import sys
from setuptools import setup, find_packages

#: Common requirements
install_requires = [
     'enaml>=0.10',  # must install pyqt or pyside
     'twisted',
     'enamlx',
     'pyqtgraph',
     'qtconsole',
     'pyserial>=3.4',
     'jsonpickle',
     'lxml',  # use sudo apt install libxml2-dev libxslt-dev

     # Python 2:
     'future; python_version < \'3.0\'',
     'faulthandler; python_version < \'3.0\'',
     'qt4reactor; python_version < \'3.0\'',

     # Python 3:
     'PyQt5; python_version >= \'3.0\'',
     'qt5reactor; python_version >= \'3.0\'',

     # Linux:
    'pycups; sys_platform == \'linux2\'',
    'pycups; sys_platform == \'linux\'',

     # Windows:
    'pywin32; sys_platform == \'win32\''
];


setup(
    name='inkcut',
    packages=find_packages(),
    include_package_data=True,
    version="2.0.7dev",
    author="CodeLV",
    author_email="frmdstryr@gmail.com",
    license='GPLv3',
    url='https://github.com/codelv/inkcut/',
    description="An application for controlling 2D plotters, cutters, "
                "engravers, and CNC machines.",
    long_description=open("README.md").read(),
    entry_points={
        'console_scripts': ['inkcut = inkcut.app:main'],
    },
    install_requires=install_requires,

)
