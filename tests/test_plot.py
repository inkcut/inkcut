#!/usr/bin/env python
"""Test suite to test the plot.py file"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'app'))
import inkcut

from lxml import etree

from lib.plot import Plot

log = logging.getLogger(__name__)
class TestPlot:
    def setUp(self):
        """Setup the Inkcut database and other application settings"""
        pass

    def tearDown(self):
        pass

    def test_case_1(self):
        """material width and length"""
        job = Job(source_filename=self.file1)
        job.material = self.material
        assert job.material.width==38.1
        assert job.material.length==4572

    def test_case_2(self):
        """job loaded source file"""
        filename = 'box.svg'
        job = Job(source_filename=self.file1)
        log.info(job.messages)
        assert job.load()

    def test_case_3(self):
        """job source is an etree element"""
        job = Job(source_filename=self.file1)
        assert job.load()
        log.info(type(job.source))
        assert type(job.source) == etree._ElementTree

    def test_case_5(self):
        job = Job(source_filename=self.file1)
        job.material = self.material
        assert job.data==job.source


