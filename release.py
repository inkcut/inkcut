"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file COPYING.txt, distributed with this software.

Created on Dec 5, 2017

@author
"""
import os
import sys
import importlib
from glob import glob
from os.path import dirname, split
from cx_Freeze import setup, Executable
from cx_Freeze import Executable, hooks, setup
from cx_Freeze.hooks.qthooks import (
    IS_WINDOWS,
    QtHook,
    _get_qt_files,
    _qt_implementation,
)


def find_enaml_files(*modules):
    """ Find .enaml files to include in the zip """
    files = {}
    for name in modules:
        mod = importlib.import_module(name)
        mod_path = dirname(mod.__file__)
        pkg_root = dirname(mod_path)

        for file_type in ['enaml', 'png']:
            for f in glob('{}/**/*.{}'.format(mod_path, file_type),
                          recursive=True):
                pkg = f.replace(pkg_root+os.path.sep, '')
                files[f] = pkg

    return files.items()


def find_data_files(*modules):
    files = {}
    for name in modules:
        mod = importlib.import_module(name)
        mod_path = name#mod.__file__# if hasattr(mod, '__file__') else name
        pkg_root = name#dirname(mod_path)

        for f in glob('{}/**/*.png'.format(mod_path), recursive=True):
            pkg = f.replace(pkg_root+os.path.sep, '')
            files[f] = pkg
    return files.items()


setup(
  name='Inkcut',
  author="Inkcut team",
  author_email="frmdstryr@gmail.com",
  license='GPLv3',
  url='https://github.com/inkcut/inkcut/',
  description="An application for controlling 2D plotters",
  long_description=open("README.md").read(),
  version='1.0',
  install_requires=[
      'PyQt5', 'enaml', 'enamlx', 'QScintilla', 'autobahn',
      'qt5reactor', 'qtconsole', 'jsonpickle', 'pozetron-cli', 'jedi',
      'pyserial',
  ],
  options=dict(
      build_exe=dict(
          packages=[
              'inkcut',
              'enaml',
              'enamlx',
              'pygments',
              'ipykernel',
              'zmq'
          ],
          zip_include_packages=[
              'atom',
              'asn1crypto', 'asyncio', 'attr', 'autobahn', 'automat',
              'collections', 'concurrent', 'constantly', 'ctypes', 'curses',
              'cffi', 'cryptography',
              'dateutil', 'dbm', 'distutils',
              'email', 'enaml', 'enamlx', 'encodings',
              'html', 'http',
              'idna', 'importlib', 'incremental', 'ipykernel', 'IPython',
              'ipython_genutils',
              'jedi', 'json', 'jsonpickle', 'jupyter_client', 'jupyter_core',
              'logging', 'libfuturize',
              'multiprocessing',
              'OpenSSL',
              'parso', 'past', 'pexpect', 'pkg_resources', 'ply',
              'prompt_toolkit', 'ptyprocess', 'pydoc_data', 'pyflakes',
              'pygments', 'pycparser',
              'qtconsole', 'qt5reactor', 'qtpy',
              'sqlite3', 'setuptools', 'serial',
              'traitlets', 'traitlets', 'txaio', 'tornado',
              'tkinter', 'test',
              'unittest', 'urllib',
              'wcwidth',
              'xml', 'xmlrpc',
              #'zmq',
          ],
      )
  ),
  executables=[
       Executable(
        "main.py",
        base="gui",
        icon="inkcut/res/icons/logo." + ("ico" if IS_WINDOWS else "png"),
        target_name="inkcut",
        shortcut_name="Inkcut" if IS_WINDOWS else None,
        shortcut_dir="DesktopFolder" if IS_WINDOWS else None,
    )
  ]
)
