Inkcut now embeds an IPython console which greatly helps debugging. You can
access the entire runtime state of the application via python's inspection
tools and the enaml [workbench](https://enaml.readthedocs.io/en/latest/dev_guides/workbenches.html)'s
plugin api.


It's often helpful to be able to manually send commands the the device.

To do this from the console use:


```python
from inkcut.core.workbench import InkcutWorkbench
# Get device handle
device = InkcutWorkbench.instance().get_plugin('inkcut.device').device
device.connect() # Or click the connect button in the Control tab
device.connection.write("D100,100")

# Some time later...
device.disconnect()

```

You can use this to run scripts if needed. See the [IPython docs](https://ipython.readthedocs.io/en/stable/index.html)
for more on IPython.

> Note: Since Inkcut does not use threads writing is all asyncronously. To wait
for a write to complete, use the returned [deferred](https://twisted.readthedocs.io/en/latest/core/howto/defer-intro.html)
