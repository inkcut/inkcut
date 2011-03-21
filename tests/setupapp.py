#!/usr/bin/env python
"""Setup the inkcut application"""
import sys
import os
import logging

dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__))),'inkcut'))

import inkcut
app = inkcut.Application()

from inkcut.lib.meta import Session, Base

from inkcut.lib.job import Job
from inkcut.lib.device import Device
from inkcut.lib.material import Material


log = logging.getLogger(__name__)

def setup_app(command, conf, vars):
    """Place any commands to setup vinylmark here"""
    # Don't reload the app if it was loaded under the testing environment
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    try:
        # Create the tables if they don't already exist
        Base.metadata.drop_all(checkfirst=True, bind=Session.bind)
        Base.metadata.create_all(bind=Session.bind)
        
        # Add some stuff the the db
        log.info("Create groups")
        Session.add(Group(u"Admins"))

        log.info("Create basic roles")
        Session.add(Role(u"Admin"))
        
        log.info("Create a grouped few users")
        # A group has all permissions we need, so we don't need any roles here, i think
        Session.add(User(username="admin",password="easybake",email="mail@vinylmark.com",group_id=1))

        log.info("Create a template")
        Session.add(Template(name='Default',path='/ebay/default.mako'))
        
        log.info("Create a listing")
        l = Listing(
            None,
            1,
            u'Vinyl Gun Wrap Kit',
            u'This auction is for 12" by 15" sheet of gun decals. (over 60 guns)  These gun decals are designed and made professionally with high quality 7 year vinyl.  Decals are perfect for Xbox 360, Playstation 3 (PS3), Wii, snowboards, skateboards, computer cases, laptops, game consoles, windows, bikes, anything you can imagine. ',
            u'# 60+ Individual Stickers # 20+ Different Guns # 5 Year Intermediate Vinyl # Easy to apply'
        )
        
        log.info("Add colors")
        c = Color(name="Matte White",text='#555',border='#ccc')
        l.colors.append(c)
        c = Color(name="Gloss White",text='#555',border='#ccc')
        l.colors.append(c)
        c = Color(name="Matte Black",text='#111',border='#111',background='#111')
        c = Color(name="Gloss Black",text='#000',border='#000',background='#000')
        l.colors.append(c)
        
        log.info("Add images")
        img = Image(url='https://sites.google.com/site/vinylmarkllc/listings/P1010582.JPG',listing_id=1)
        l.images.append(img)
        img = Image(url='https://sites.google.com/site/vinylmarkllc/listings/P1010566.JPG',listing_id=1)
        l.images.append(img)
        img = Image(url='https://sites.google.com/site/vinylmarkllc/listings/P1010561.JPG',listing_id=1)
        l.images.append(img)
        img = Image(url='https://sites.google.com/site/vinylmarkllc/listings/P1010557.JPG',listing_id=1)
        l.images.append(img)
        
        Session.add(l)
        Session.commit()
        log.info("Successfully set up.")
    except Exception, e:
        log.info("Error: Setting up the databases failed: %s"%e)
        raise

