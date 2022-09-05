### Install

#### Install dependencies

Inkcut requires python. To install inkcut, we use the `pip` tool.
On Linux and OSX, the cups printer drivers and pyside GUI bindings are required as well.

##### Windows

This documentation is still pending.

##### Linux

For example on ubuntu or the raspberry pi:

```bash

apt-get install python3-pip python3-pyqt5 python3-setuptools libcups2-dev python3-pyqt5.qtsvg
pip3 install inkcut

```

To upgrade to the latest release

```bash

pip3 install --upgrade inkcut

```

To install the latest dev version from github use

```bash

pip3 install git+https://github.com/codelv/inkcut.git

```

If you use the serial interface, you also need to add your user to the `dialout` group:

```bash
sudo usermod -a -G dialout "$USER"
```

Otherwise, you might get this error:

```bash
Permission denied: '/dev/ttyS1'
```

##### OSX

Install brew if you don't already have it from https://brew.sh/

Next install python 3 and pyqt with

```bash

brew install python3
brew install pyqt

```

finally install inkcut

```bash

pip3 install inkcut

```

### Running

To use the installed version simply run `inkcut`

### Installing as Inkscape extension

1. Download the extension files from Inkcut's extension page from the [Inkscape extension list](https://inkscape.org/en/~frmdstryr/%E2%98%85inkcut) or from the `plugins/inkscape` folder from this repository
2. Copy them to `~/.config/inkscape/extensions`
3. Restart Inkscape
4. Inkcut will be added to the Extensions menu
