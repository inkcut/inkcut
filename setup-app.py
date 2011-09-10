#!/usr/bin/env python
"""Setup the inkcut application"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'app'))

from inkcut import Inkcut
from lib.meta import Session, Base

from lib.job import Job
from lib.device import Device
from lib.material import Material


log = logging.getLogger(__name__)

def setup_app():
    """Setup the Inkcut database and other application settings"""
    app = Inkcut()
    try:
        # Create the tables if they don't already exist
        Base.metadata.drop_all(checkfirst=True, bind=app.session.bind)
        Base.metadata.create_all(bind=app.session.bind)

        # Add some stuff the the db
        log.info('Create Materials')
        material = Material(name=u'3M 180C White',
            cost=.47,width=38.1,length=100,
            velocity=16,force=80,color=u'#FFF'
        )
        app.session.add(material)

        material = Material(name=u"3M 180C Black",
            cost=.47,width=38.1,length=100,
            velocity=16,force=80,color=u'#000'
        )
        app.session.add(material)

        material = Material(name=u"Avery 900 Ultimate Cast Metallic Red",
            cost=1.23,width=38.1,length=100,
            velocity=4,force=100,color=u'#BE3934'
        )
        app.session.add(material)

        material = Material(name=u"Generic 12\" Vinyl Roll",
            cost=0.23,width=38.1,length=None,color=u'#FFFFFF'
        )
        app.session.add(material)

        material = Material(name=u"Generic 24\" Vinyl Roll",
            cost=1.23,width=76.2,length=None,margin=(20,20,20,20),
            color=u'#626FF1'
        )
        app.session.add(material)

        app.session.commit()
        log.info("Successfully set up.")
    except Exception, e:
        log.info("Error: Setting up the databases failed: %s"%e)
        raise

if __name__ == "__main__":
    setup_app()
