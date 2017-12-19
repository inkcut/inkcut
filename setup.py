"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Dec 15, 2017

@author: jrm
"""

from setuptools import setup, find_packages

setup(
    name='inkcut',
    packages=find_packages(),
    version="2.0.3",
    author="CodeLV",
    author_email="frmdstryr@gmail.com",
    license='GPLv3',
    url='https://github.com/codelv/inkcut/',
    description="An application for controlling 2D plotters, cutters, "
                "engravers, and CNC machines.",
    long_description=open("README.md").read(),
    entry_points={
        'console_scripts': ['inkcut = inkcut.app.main'],
    },
    install_requires=[
        'PyQt5',  # Only works on Python 3
        'enaml',  # must install pyqt or pyside
        'twisted',
        'enamlx',  # use pip install git+https://github.com/frmdstry/enamlx.git
        'pyqtgraph',
        'qt5reactor',  # Use qt4reactor on 2.7
        'qtconsole',
        'pyserial',
        'jsonpickle',
        'lxml',  # use sudo apt install libxml2-dev libxslt-dev
        #'future',  #: Only for 2.7
        #'faulthandler', #: Onl for 2.7
    ],
)
