import sys
import os
import logging
dirname = os.path.dirname
sys.path.append(os.path.join(os.path.abspath(dirname(dirname(__file__)))))
from lxml import etree
from lib.plot import Plot
logging.basicConfig()
log = logging.getLogger(__name__)


plot = Plot(90*12*16,90*12*4)
plot.set_graphic(etree.tostring(etree.parse("tests/fat-giraffes.svg")))
plot.set_copies(40) # two horizontal stacks and one extra
#f = open("out/plot_%s.svg"%sys._getframe().f_code.co_name,"w")
#f.write(plot.get_preview_xml())
