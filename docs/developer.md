### Developer

This is documentation is intended for developers wishing to modify or extend Inkcut. 

### Building from source

To build from source use the commands below.

We intend to support both Python 2 (with qt 4) and Python 3 (with qt 5), however using Python 3 is recommended. On 32-bit systems only Python 2 works, since PyQt5 only has a 64-bit package.

#### Python 3 (Recommended)

```bash

virtualenv -p python3 venv
source venv/bin/activate

# Install lxml
sudo apt install libxml2-dev libxslt-dev

#: Install inkcut
pip install .

```
##### NOTES:
1. Install commands should be run from the folder Inkcut is cloned/downloaded into using either `cd /path/to/inkcut/folder`
2. If `pip install . ` gives an error regarding enamlx, you may need to install enamlx, then re-run `pip install . `
In Ubuntu 16, this can be done by: `pip install git+https://github.com/frmdstryr/enamlx.git`.

#### Python 2

```bash

virtualenv -p python2 venv
source venv/bin/activate

# Install lxml
sudo apt install libxml2-dev libxslt-dev

# Only on Python 2 - you must install and link pyqt4
sudo apt install python-qt4

#: Replace ~/.virtualenvs/cv with venv/ on linux
ln -s /usr/lib/python2.7/dist-packages/PyQt4/ ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/sip.so ~/.virtualenvs/cv/lib/python2.7/site-packages/

#: Install inkcut
pip install .

```


#### Raspberry pi

```bash

source ~/.profile           #" loads virtual environment profile settings
workon cv                   #" opens virtual environment cv

# Install lxml
sudo apt install libxml2-dev libxslt-dev

# Only on Python 2 - you must install and link pyqt4
sudo apt install python-qt4

#: Replace ~/.virtualenvs/cv with venv/ on linux
ln -s /usr/lib/python2.7/dist-packages/PyQt4/ ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/sip.so ~/.virtualenvs/cv/lib/python2.7/site-packages/

#: Install inkcut
pip install .

# On the raspberry pi, install RPI.GPIO (if using the motor control driver)
pip install RPi.GPIO

# Install zbar (pi only for crop mark registration)
pip install git+https://github.com/npinchot/zbar.git

```


### Plugins

Inkcut is designed entirely using plugins using enaml's workbench framework. 
The inkcut source is separated into packages where each is a plugin (and any plugins 
that plugin adds).  

The default plugins allow developers to define:

- New dock items
- Menu items and commands
- Cli commands and hooks
- New device drivers
- Device protocols
- Special connection types

These plugins can interact with all builtin plugins using the enaml workbench interface.


### External plugins

You can define plugins and install them using python entry points. 
Inkcut loads external plugins from the `inkcut.plugin` entry point. Using this you can 
create python packages usesrs can install to extend Inkcut. The entry point implementation 
shall return an enaml `PluginManifest` factory (either the PluginManifest subclass or a 
function that when called returns a PluginManifest instance).   

> See a nice intro on entry points here [using-plugins](https://docs.pylonsproject.org/projects/pylons-webframework/en/latest/advanced_pylons/entry_points_and_plugins.html#using-plugins)


### Device extensions

Inkcut was redesigned to have separation between the device job processing, 
device connection, the protocol used, and the configuration of each. All of these 
can be completely customized as is needed for your specific hardware. 

This extensibility should allow Inkcut to be used for more than vinyl cutters and 
plotters as discussed below. 

##### Device drivers

Custom device "drivers" can be implemented to enable Inkcut to control specific device. 
A custom stepper motor driver for Inkcut using the raspberry pi demonstrates the usage of 
this. DeviceDrivers must implement the [Device](../inkcut/device/extensions.py) interface.

The driver may have it's own configuration and UI for editing the configuration without
needing to modify any core functionality. Adding a driver is done by simply registering
it with a plugin.

A driver may also transform, manipulate, and do any post processing of a path before it
is sent to the device. The actual connecting, sending, and processing can all be 
overridden as is needed by the driver.


##### Protocols

If the builtin driver is sufficient for processing the job but uses a custom
communication protocol. The custom protocol can be added as an external plugins or to the
builtin device protocols (such as HPGL, DMPL, etc.. ) in the 
[inkcut.device.protocols](../inkcut/device/protocols/manifest.enaml) plugin.
The protocol must implement the basic [DeviceProtocol](../inkcut/device/plugin.py) interface.

The protocol may have it's own configuration options and UI for editing the options 
without needing to modify any core functionality.

##### Connections

Connections (such as Serial port, Printer, etc.. ) are added in the 
[inkcut.device.transports](../inkcut/device/transports) packages. Connections
are simply an interface used to communicate with "some device". 

Serial and printer connections are included by default. More can be added by external plugins. 
The plugin must implement the basic [DeviceTransport](../inkcut/device/plugin.py) interface.

Each connection may have it's own configuration and UI for editing the configuration 
without needing to modify any core functionality.


##### Filters

Filters are used to do preprocessing of the job before it is converted to commands 
to be sent to the device. Examples of filters are `blade offset` and `overcut` 
compensation. 

New filters should be added to the [inkcut.device.filters](../inkcut/device/filters) packages. 
Or they can be added by external plugins. The plugin must implement the basic 
[DeviceFilter](../inkcut/device/plugin.py) interface. 

Filters are applied to the "path model" (QPainterPath) either before or after
it is converted to a polygon for sending to the device.

Each filter may have it's own configuration and UI for editing the configuration 
without needing to modify any core functionality.

### Jobs

Inkcut now uses the concept of a "Job" to represent an SVG graphic and the configuration
settings required to create the final output. The core piece of this is the svg parser
that generates a QPainterPath. The QPainterPath is used to internally represent
the paths that must eventually be sent to the device.

### Contributing

Contributions are welcome. Please document any enhancements using markdown. 
New pages can be added to the `site.json` in the docs folder and can link to 
markdown files. The project website updates it's cached pages after about an hour.  

#### How to use markdown

See [mastering-markdown](https://guides.github.com/features/mastering-markdown/)


#### Pushing changes with git

Cd to the folder and

    :::bash
    
    git add <file/path>
    git commit -m "Some message"
    git push origin master
    
    #: Config is in .git/config

### Releasing

Build:

    :::bash
    
    rm -r dist
    python setup.py sdist
    python setup.py bdist_wheel --universal

To do a test release:

    :::bash
    
    twine upload --repository-url https://test.pypi.org/legacy/ dist/*

Then install and test it (on other machines) with:

    :::bash
    
    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple inkcut

To do the actual release:

    :::bash
    
    twine upload dist/*

See also:

* https://packaging.python.org/tutorials/distributing-packages/
* https://packaging.python.org/guides/using-testpypi/#using-test-pypi

### Donations

I put a lot of work into this project. Initial development started in 2015 and Inkcut was
completely rewritten 4 times since then, improving every iteration.  Please consider
donating or sponsoring the development of Inkcut [here](https://www.codelv.com/projects/inkcut/support/).

