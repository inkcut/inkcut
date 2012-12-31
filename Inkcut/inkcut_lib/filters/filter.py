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
import tempfile
import os
import logging
logger = logging.getLogger('inkcut')

from inkcut_lib.geom import geom,bezmisc

class Filter(object):
    """
    Base class for defining an Inkcut plugin.  There are two modes: input
    and output.  An input plugin is used for converting filetype x into an
    SVG file, which is then read by Inkcut. An output plugin is used for
    converting a SVG file into an output filetype.
    """
    name = "Default Filter (No Conversion)"
    infiletypes = ['hpgl']
    outfiletype = 'hpgl'

    def __init__(self,infile=None,outfile=None,preferences={}):
        assert os.path.isfile(infile), "Infile must be a readable file! Given %s"%infile
        self.infile = infile

        # Create an output file if one doesn't exits
        if outfile:
            self.outfile = outfile
        else:
            out = tempfile.NamedTemporaryFile(delete=False)
            #out.close()
            self.outfile = out.name
            
        self.preferences = preferences

    def run(self):
        """ Copies self.input to self.output. """
        with open(self.outfile,'w') as out:
            with open(self.infile) as f:
                for line in f:
                    out.write(line)

    # ====================== Common Export Functions ==========================
    @classmethod
    def apply_cutting_overcut(cls,data,overlap):
        """
        Applies an overcut to data from Graphic.get_polyline(). Returns None.
        Note: this only supports polylines at the moment!
        Todo: Add support for curves and arcs
        """
        assert type(overlap) in [int, float], "Overlap must be an int or float. Got %s" % type(overlap)
        assert overlap >= 0, "Overlap cannot be a negative value. Got %s" %overlap
        if overlap <= 0:
            return
        for i in range(0,len(data)):
            path = data[i]
            if path_is_closed(path):
                overlap_left = overlap
                j=0
                while overlap_left > 0 and j < len(path)-1:
                    distance = geom.point_distance(path[j][1],path[j+1][1])
                    if overlap_left > distance:
                        path.append(path[j+1])
                    else: # last point
                        path.append(['L',list(bezmisc.tpoint(path[j][1],path[j+1][1],overlap_left/distance))])
                    overlap_left -= distance
                    j += 1
    """
    @classmethod
    def apply_overcut(cls,data,overcut):
        #Applies an overcut to data from Graphic.get_data(). Returns None.
        #Todo: Add support for curves and arcs
        assert type(overcut) in [int, float], "Overlap must be an int or float. Got %s" % type(overlap)
        assert overcut >= 0, "Overlap cannot be a negative value. Got %s" %overlap
        if overcut <= 0:
            return
        for i in range(0,len(data)):
            path = data[i]
            if path_is_closed(path):
                left = overcut
                j=0
                while left > 0 and j < len(path)-1:
                    distance = geom.point_distance(path[j][1],path[j+1][1])
                    if overlap_left > distance:
                        path.append(path[j+1])
                    else: # last point
                        path.append(['L',list(bezmisc.tpoint(path[j][1],path[j+1][1],left/distance))])
                    overlap_left -= distance
                    j += 1
    """
    @classmethod
    def apply_cutting_blade_offset(cls,data,offset,smoothness,angle=165):
        """
        Applies a cutting blade offset to data from Graphic.get_data_array().
        Returns None. This should be applied after all cutting order
        sorting is applied since it depends the on path order.
        Purpose:
            The blade is always trailing the pen position, that means when
            the pen does a hard corner, the corner gets cut off.  The purpose
            of this is to eliminate this.

        Method:
            In order to do this, we have to extend each line of the polyline
            by the offset amount and then return back to the original line.

            The pen can rotate around a circle of radius=offset without
            cutting anything (ideally, there actually is a width of the
            blade so this isn't 100% true) which means if we cut past
            by a distance offset we can bring the pen back to the direction
            of the next line by moving along the arc between the two lines.
        
        """
        assert type(offset) in [int, float], "offset must be an int or float. Got %s" % type(offset)
        assert offset >= 0, "offset cannot be a negative value. Got %s" %offset
        #eps = 1 # this  is assuming after scaling!
        max_theta = angle*0.017453292 # convert deg to radians
        if offset <= 0:
            return

        def get_line_offset_fix(p0,p1,p2,offset=offset,max_angle=max_theta):
            """ Returns a new command to fix the blade offset. """
            v1 = geom.subtract(p0,p1)
            v2 = geom.subtract(p2,p1)
            if (not geom.point_equal(v1,v2)) and geom.norm(v1)>0 and geom.norm(v2)>0:
                # only apply if an offset if angle is great enough
                t2 = offset/geom.norm(v2)
                if (geom.angle_between(v1,v2) < max_angle) and t2<1:
                    t1 = 1+offset/geom.norm(v1) # extend
                    pt1 = list(bezmisc.tpoint(p0,p1,t1))
                    pt2 = list(bezmisc.tpoint(p1,p2,t2))
                    # TODO: THIS SHOULD USE A CURVE TO WORK BETTER!
                    return [['L',pt1],['L',pt2]]
            return []
        
        def get_curve_to_line_offset_fix((p0,c0,c1,p1),p2,offset=offset,max_angle=max_theta,smoothness=smoothness):
            """ Returns a new command to fix the blade offset. """
            curve = (p0,c0,c1,p1)
            v1 = geom.subtract(c1,p1)
            v2 = geom.subtract(p2,p1)
            
            # get the point one curve segment before p1
            #l = bezmisc.bezierlengthSimpson(curve)
            t = .5
            
            # vector from p1 to this point
            v0 = geom.subtract(bezmisc.bezierpointatt(curve,t),p1)
            
            if  geom.norm(v0)>0 and geom.norm(v2)>0:
                # only apply if an offset if angle is great enough
                t2 = offset/geom.norm(v2)
                if (geom.angle_between(v0,v2) < max_angle) and t2<1:
                    
                    # extend using the second control point since it's tangent
                    t1 = 1+offset/geom.norm(v1) # extend
                    pt1 = list(bezmisc.tpoint(c1,p1,t1))
                    pt2 = list(bezmisc.tpoint(p1,p2,t2))
                    # TODO: THIS SHOULD USE A CURVE TO WORK BETTER!
                    return [['L',pt1],['L',pt2]]
            return []
        
        def get_curve_offset_fix(p0,p1,p2,p3,p4,offset=offset,max_angle=max_theta):
            """ Returns a new command to fix the blade offset. 
            p0 & p1 define the line, p1, p2, p3, p4 define the curve
            """
            curve = (p1,p2,p3,p4)
            v1 = geom.subtract(p0,p1)
            v2 = geom.subtract(p2,p1)
            if (not geom.point_equal(v1,v2)) and geom.norm(v1)>0 and geom.norm(v2)>0:
                # only apply if an offset if angle is great enough
                t2 = offset/bezmisc.bezierlengthSimpson(curve)
                if (geom.angle_between(v1,v2) < max_angle) and t2<1:
                    t1 = 1+offset/geom.norm(v1) # extend
                    pt1 = list(bezmisc.tpoint(p0,p1,t1))
                    
                    c = bezmisc.beziersplitatt(curve,t2)[1]
                    new_curve = []
                    for p in c[1:]:
                        new_curve.extend(p)
                    # TODO: THIS SHOULD USE A CURVE TO WORK BETTER!
                    # insert extend point, then adjust curve to new start point
                    return [['L',pt1],['L',c[0]],['C',new_curve]]
            return []
       
        # control points    
        pstart = (0,0)
        pprev = (0,0) 
        pcur = (0,0)
        
        
        #logger.debug(pformat(data))
        
        i=0
        while i < len(data)-1:
            cmd,params = data[i]
            cnext = data[i+1][0]
            if cmd == 'M': 
                pprev = params[-2:]
                pstart = pprev
            elif cmd == 'L' and cnext in ['L','Z']:
                """
                Replace pcur by pcur extended by offset and insert a
                point returning back to on track to pnext.
                """
                pcur = params[-2:]
                pnext = (cnext == 'Z' and pstart) or data[i+1][1][:2]
                fix = get_line_offset_fix(pprev,pcur,pnext)
                if len(fix)>0:
                    data.pop(i) # remove current point
                    for segment in fix:
                        data.insert(i,segment)
                        i+=1
                    i-=1 # adjust for the pop
                pprev = params[-2:]
            elif cmd == 'L' and cnext == 'C':
                """
                Extend L by offset, then come back to curve at T
                """
                pcur = params[-2:]
                fix = get_curve_offset_fix(pprev,pcur,data[i+1][1][:2],data[i+1][1][2:4],data[i+1][1][-2:])
                if len(fix)>0:
                    data.pop(i)
                    for segment in fix:
                        data.insert(i,segment)
                        i+=1
                    data.pop(i) # remove old curve
                    i-=2
                pprev = params[-2:]
            elif cmd == 'L':
                pprev = params[-2:]
            elif cmd == 'C' and cnext in ['L', 'Z']:
                """
                Same as L to L but uses control point to end point of curve
                as first vector (p0 to p1).
                """
                pnext = (cnext == 'Z' and pstart) or data[i+1][1][:2]
                fix = get_curve_to_line_offset_fix((pprev,params[:2],params[2:4],params[-2:]),pnext)
                if len(fix)>0:
                    for segment in fix:
                        i+=1
                        data.insert(i,segment)
                pprev = params[-2:]
            elif cmd =='C' and cnext == 'C':
                pprev = params[2:4]
                pcur = params[-2:]
                fix = get_curve_offset_fix(pprev,pcur,data[i+1][1][:2],data[i+1][1][2:4],data[i+1][1][-2:])
                if len(fix)>0:
                    for segment in fix:
                        i+=1
                        data.insert(i,segment)
                    data.pop(i) # remove old curve
                    i-=1
                pprev = params[-2:]
            elif cmd =='C':
                pprev = params[-2:]
            elif cmd == 'Z':
                # last point in path, skip
                pprev = pstart
            i+=1
        """
        Cases:
        M to L - n/a
        M to C - n/a
        L to L - works
        L to Z - works
        L to C - not yet! (why not?)
        C to L - works!
        C to Z - works!
        C to C - not yet
        L to Z - works
        """
        #logger.debug('\n\n\n\n\n')
        #logger.debug(pformat(data))
        
    # ===================== UI & Error Handling ===============================
    def handle_failure(self,message):
        """ Prompts the user with an error message and tells Inkcut the plugin failed."""
        pass

    def alert_user(self,message,type_):
        """Used for raising errors and sending messages to the Inkcut UI """
        pass

    def prompt_user(self,message,gtk_dialog=None):
        """ Prompts the user for input with the given message type. """
        pass

# ==================== Helpful Functions ===============================
def path_is_closed(path):
    """Returns true if the first and last point are equal."""
    assert type(path) == list, "path must be a list of path segments"
    return map(lambda x: round(x,6),path[0][1]) == map(lambda x: round(x,6),path[len(path)-1][1])

