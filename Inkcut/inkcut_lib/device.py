# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2011 Jairus Martin - Vinylmark LLC <jrm@vinylmark.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE
import platform
import os
import serial
import time
import traceback

CONNECTION_TYPES = ['Serial','Printer']
CURVE_QUALITY = ['Very High','High','Normal','Low','Very Low']
BAUDRATES = [50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200,230400, 460800, 500000, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000]
BYTESIZE = ['8','7','6','5']
PARITY = ['None','Odd','Even','Mark','Space']
STOPBITS = ['1','1.5','2']
PACKET_SIZES = ['B','KB','MB']
bytesize_map = {'8':serial.EIGHTBITS,'7':serial.SEVENBITS,'6':serial.SIXBITS,'5':serial.FIVEBITS}
parity_map = {'None':serial.PARITY_NONE,'Odd':serial.PARITY_ODD,'Even':serial.PARITY_EVEN,'Mark':serial.PARITY_MARK,'Space':serial.PARITY_SPACE}
stopbit_map = {'1':serial.STOPBITS_ONE,'1.5':serial.STOPBITS_ONE_POINT_FIVE,'2':serial.STOPBITS_TWO}

DEFAULT_PROPERTIES = { # Use this as a schema
    "name":"New Device",#str
    "width":"48.0in",#float
    "length":"36.0in",#float
    "uses_roll":True,
    "rotation":False,
    "use_cutting_force":True,
    "cutting_force":"80g",#int with %10 == 0
    "use_cutting_speed":True,
    "cutting_speed":"12cm/s",#int with with %4 == 0
    "use_material_settings":True,
    "connection_type":"Serial",
    "printer_name":"",#str
    "serial_port":"/dev/ttyUSB0",#str
    "serial_baudrate":9600,#int in BAUDRATES
    "serial_bytesize":'8',#str in PARITY
    "serial_parity":"None",#str
    "serial_stopbits":'1',#str
    "serial_xonxoff":False,
    "serial_rtscts":False,
    "serial_dsrdtr":False,
    "data_packet_size":"4096B",#int with %10 == 0
    "resolution":"1016.0steps/in",#float
    "laser_x_offset":"0.0in",#float
    "laser_y_offset":"0.0in",#float
    "long_edge_cal":"0.0in",#float
    "cal_scale_x":1,
    "cal_scale_y":1,
    "short_edge_cal":"0.0in",#float
    "curve_quality":"Normal",#str
    "use_blade_offset":True,
    "blade_offset":"0.25mm",#float
    "use_path_overcut":True,
    "path_overcut":"5.0mm",#float
    "cmd_language":"HPGL",#str in get_cmd_languages()
    "use_cmd_before":True,
    "cmd_before":"IN;",#str
    "use_cmd_after":False,
    "cmd_after":"",#str
}

HPGL_CMDS = ['IN','SP','FS','VS','PU','PD','PA','PR'] # many more are ignored...

class Pen():
    def __init__(self,x=0,y=0,z=0):
        self.x = x
        self.y = y
        self.z = z

class Device():
    """
    Interface to communcate with a plotter or cutter as well as get
    properties such as width, length, speed, status etc.
    """

    def __init__(self,properties):
        """Create a device instance with it's properties."""
        p = DEFAULT_PROPERTIES
        p.update(properties)
        for k,v in p.iteritems():
            setattr(self,k,v)
        # now we can use self.name, etc...
        self.jobs = []
        self.pen = Pen()
        self.status = {'state':'idle','data_sent':0,'eta':0,'filesize':0,'fraction':0}
        
    @staticmethod
    def get_printers():
        """Returns a list of printers installed on the system."""
        if platform.system() == 'Linux':
            #if round(time.time()%2)==0: #Testing the no devices message!
            #    return []
            try:
                import cups
                con = cups.Connection()
                return con.getPrinters()
            except:
                print traceback.format_exc()
                return []
            
        elif platform.system() == 'Windows':
            return []
            
    @staticmethod
    def get_serial_ports():
        """Returns a list of serial port names available on the system."""
        if platform.system() == 'Linux':
            import scanlinux
            return scanlinux.scan()
        elif platform.system() == 'Windows':
            import scanwin32
            ports = []
            for order, port, desc, hwid in sorted(scanwin32.comports(False)):
                ports.append(port)
            return ports

    @staticmethod
    def get_printer_by_name(name):
        """Returns a list of printers installed on the system."""
        for printer in Device.get_printers():
            if printer.name == name:
                return printer
    
    def schedule(self,filename):
        """Schedule a job to the device.  This is used so the actual
        process can be controlled by a UI. Right now a job is only 
        a filename, this could be scaled to include any more things...
        """
        self.jobs.append(filename)
    
    def execute(self):
        """Generator that executes the first job in the job stack."""
        job = self.jobs.pop()
        #unit = self.data_packet_size[-2:]
        buffer_size = 8#int(self.data_packet_size[:-2])*10**((unit==PACKET_SIZES[2] and 6) or (unit==PACKET_SIZES[1] and 3) or 0) # converts to MB or KB
        self.status['filesize'] = os.path.getsize(job)
        self.status['data_sent'] = 0
        self.status['state'] = 'running'
        
        with open(job) as f:
            while self.status['state'] in ['running','paused']: # will break if state == 'cancelled'
                if self.status['state'] == 'paused': # if paused, dont send any data
                    time.sleep(1)
                    yield True
                else:
                    data = f.read(buffer_size)
                    if data:
                        # TODO: update Pen with position of data!
                        self.status['data_sent'] += self.write(data)
                        self.status['fraction'] = self.status['data_sent']/float(self.status['filesize'])
                        yield True
                    else:
                        self.status['state'] = 'idle'
                        yield False
        
        yield False
                    
    def connect(self):
        if self.connection_type == 'Serial':
            s = serial.Serial(
                    port=self.serial_port, 
                    baudrate=int(self.serial_baudrate), 
                    bytesize=bytesize_map[self.serial_bytesize], 
                    parity=parity_map[self.serial_parity], 
                    stopbits=stopbit_map[self.serial_stopbits], 
                    timeout=5, 
                    xonxoff=self.serial_xonxoff, 
                    rtscts=self.serial_rtscts, 
                    writeTimeout=5, 
                    dsrdtr=self.serial_dsrdtr, 
                    interCharTimeout=5
                )
            s.open()
            self.s = s
        
    def disconnect(self):
        if hasattr(self,'s'):
            self.s.close()    
        
    def write(self,data):
        """ General interface for sending data to the device """
        if self.connection_type != 'Serial':
            if platform.system() == 'Linux':
                printer = os.popen('lpr -P %s'%(self.name),'w')
                #TODO: Insert buffer here...
                printer.write(data)
                printer.close()                
            elif platform.system() == 'Windows':
                pass
                # pywin32 or something here...
        else:
            return self.s.write(data)
        

def port_scan():
    """scan for available ports. return a list of tuples (num, name)"""
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append( (i, s.portstr))
            s.close()   # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
    return available
