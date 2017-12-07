"""
Copyright (c) 2017, Jairus Martin.

Distributed under the terms of the GPL v3 License.

The full license is in the file LICENSE, distributed with this software.

Created on Jul 12, 2015

@author: jrm
"""
import os
import enaml
from atom.api import Instance, Enum, List
from inkcut.core.api import Plugin, unit_conversions, log

from .models import Job, JobError, Material


class JobPlugin(Plugin):

    #: Units
    units = Enum(*unit_conversions.keys())

    #: Available materials
    materials = List(Material)

    #: Current material
    material = Instance(Material, ())

    #: Previous jobs
    jobs = List(Job)

    #: Current job
    job = Instance(Job)

    def _default_job(self):
        return Job(material=self.material)

    def _default_units(self):
        return 'in'

    # -------------------------------------------------------------------------
    # Plugin API
    # -------------------------------------------------------------------------
    def start(self):
        """ Register the plugins this plugin depends on

        """
        w = self.workbench
        with enaml.imports():
            from inkcut.device.manifest import DeviceManifest
            w.register(DeviceManifest())

    # -------------------------------------------------------------------------
    # Job API
    # -------------------------------------------------------------------------
    def open_document(self, path):
        """ Set the job.document if it is empty, otherwise close and create
        a  new Job instance.
        
        """
        if not os.path.exists(path):
            raise JobError("Cannot open %s, it does not exist!" % path)

        if not os.path.isfile(path):
            raise JobError("Cannot open %s, it is not a file!" % path)

        # Close any old docs
        self.close_document()

        log.info("Opening {doc}".format(doc=path))
        try:
            self.job.document = path
        except ValueError as e:
            #: Wrap in a JobError
            raise JobError(e)

    def close_document(self):
        """ If the job currently has a "document" add this to the jobs list
        and create a new Job instance. Otherwise no job is open so do nothing.
        
        """
        if not self.job.document:
            return

        #: Copy so the ui's update
        jobs = self.jobs[:]
        jobs.append(self.job)
        self.jobs = jobs
        #: Create a new default job
        self.job = self._default_job()
