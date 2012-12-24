#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       name.py
#-----------------------------------------------------------------------
#       Copyright 2010 Jairus Martin <frmdstryr@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#-----------------------------------------------------------------------
import sys
sys.path.append('/home/rhino/projects/inkcut/app/bin')
import path

from lxml import etree
pd1 = etree.fromstring('<path style="color:#000000;fill-opacity:1;fill-rule:nonzero;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate" d="m 94.285713,29.50504 199.999997,0 0,200 -199.999997,0 0,-200 z" id="rect2826" />')
pd2 = etree.fromstring('<path style="color:#000000;fill-opacity:1;fill-rule:nonzero;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate" d="m 886.28986,394.24927 0,217.03271 284.60774,0 0,-217.03271 -284.60774,0 z m 92.75948,70.73974 99.08886,0 0,75.55323 -99.08886,0 0,-75.55323 z" id="rect4199" />')
pd3 = etree.fromstring('<path style="fill:none;stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" d="M 554.3556,918.44482 C 759.90318,803.2136 890.70619,937.13096 890.70619,937.13096 L 1065.1102,740.92645 728.75961,691.09673" id="path4197" />')
pd4 = etree.fromstring('<path style="color:#000000;fill:#ffff00;fill-opacity:1;fill-rule:nonzero;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate" d="M 1124.9688 349.4375 L 1061.7188 359.84375 L 1127.9062 367.21875 L 1124.9688 349.4375 z M 1052.5938 361.34375 L 844.125 395.6875 L 879.375 609.84375 L 1160.2188 563.59375 L 1138.5625 431.9375 L 1038.0938 420.75 L 1052.5938 361.34375 z M 1087.4062 383.40625 L 1082.1562 404.9375 L 1123.9375 409.59375 L 1129.1875 388.0625 L 1087.4062 383.40625 z M 1094.5938 388.59375 L 1119.9062 391.40625 L 1116.75 404.4375 L 1091.4375 401.625 L 1094.5938 388.59375 z M 1101.8125 393.75 L 1100.7188 398.28125 L 1109.5312 399.28125 L 1110.625 394.71875 L 1101.8125 393.75 z M 1044.9062 434.34375 L 1057.1875 508.84375 L 959.4375 524.96875 L 947.15625 450.4375 L 1044.9062 434.34375 z M 1028.0625 452.21875 L 968.84375 461.96875 L 976.28125 507.0625 L 1035.4688 497.3125 L 1028.0625 452.21875 z M 1011.1875 470.09375 L 1013.75 485.78125 L 993.15625 489.1875 L 990.5625 473.5 L 1011.1875 470.09375 z " id="rect4199" />')
pd5 = etree.fromstring('<path style="color:#000000;fill-opacity:1;fill-rule:nonzero;marker:none;visibility:visible;display:inline;overflow:visible;enable-background:accumulate" d="m 254.28572,360.93362 c 0,55.22848 -44.77152,100 -100,100 -55.228474,0 -99.999999,-44.77152 -99.999999,-100 0,-55.22847 44.771525,-100 99.999999,-100 55.22848,0 100,44.77153 100,100 z" id="rect2826" />')
nodes = [pd5,pd1,pd2,pd3,pd4]
g = path.Graphic(nodes)

from pprint import pprint


p = path.Path(g.data[0])
p.setScale(11.288888889)
p.setSmoothness(.14)
#pprint(p.toPolyline(.0097))
hpgl = p.toHPGL()
print hpgl
print len(hpgl)

#p.setOvercut('.01')
#pprint(p.data)

#pprint(p.data)





