#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
setup(
    name = "Inkcut",
    version = "1.1",
    packages = find_packages(),
    scripts = ['say_hello.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['docutils>=0.3'],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.txt', '*.rst'],
        # And include any *.msg files found in the 'hello' package, too:
        'hello': ['*.msg'],
    },

    # metadata for upload to PyPI
    author = "Jairus Martin",
    author_email = "jrm5555@psu.edu",
    description = "A gtk+ application for converting svg graphics to hpgl and sending them to a plotter or cutter.",
    license = "GPL",
    keywords = "inkcut, vinyl, cutting, plotting, plot, cut, sign, lettering, decal",
    url = "http://inkcut.sourceforge.net",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
