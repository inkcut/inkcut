# Inkcut

[![Gitter](https://img.shields.io/gitter/room/nwjs/nw.js.svg)](https://gitter.im/inkcut/discussion)

An application for controlling 2D plotters, cutters, engravers, and CNC machines. [Project homepage](https://www.codelv.com/projects/inkcut/)

![Inkcut - vinyl cutting and plotting](https://user-images.githubusercontent.com/380158/34273634-29e60a08-e663-11e7-9977-5125eae738f7.gif)

You can download the release versions from [here](https://github.com/codelv/inkcut/releases). 

> Note: This version is currently in alpha and only intended for testing and development purposes

### Features

- Graphic manipulation (Rotation, scaling, mirroring)
- Copy generation and layout
- Weedlines
- Inkscape integration
- Device control panel
- Job history list
- Live plot status
- Pause, resume, and abort jobs mid way
- Python 2 and 3 support (Qt5 on python 3) 
 
### Docs and tutorials

See the [project docs site](https://www.codelv.com/projects/inkcut/docs/)

#### Installing your cutter

##### Linux

###### Cutters with a parallel interface

Cutters with a parallel interface (either a 'real' parallel port or using a
built-in parallel-to-USB converter) must be added to your system as a printer
before using them from Inkcut. Start your printer configuration utility (e.g.
[system-config-printer](http://cyberelk.net/tim/software/system-config-printer)),
which at least when connecting via USB should detect the connected cutter.
Proceed to add it with a generic driver, such as 'Generic Text-Only Printer'.
Do not print a test page.

### Supported devices

See the [supported device list](https://www.codelv.com/projects/inkcut/docs/supported-devices).

Please create an issue or submit a pull request to add a device to the list.  

### Donate and support

If you use Inkcut and want to help continue the development open source cutting software 
please consider [donating](https://www.codelv.com/projects/inkcut/support/). 
