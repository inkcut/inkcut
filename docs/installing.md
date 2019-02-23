### Install

#### Install dependencies

Inkcut requires python. To install inkcut, we use the `pip` tool.
On Linux and OSX, the cups printer drivers and pyside GUI bindings are required as well.

##### Windows

This documentation is still pending.

##### Linux

For example on ubuntu or the raspberry pi:

```bash

apt-get install python3-pip python3-pyqt5 libcups2-dev
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


##### OSX

This documentation is still pending.

### Running

To use the installed version simply run `inkcut`

### Installing as Inkscape extension

1. Download the extension files from Inkcut's extension page from the [Inkscape extension list](https://inkscape.org/en/~frmdstryr/%E2%98%85inkcut) or from the `plugins/inkscape` folder from this repository
2. Copy them to `~/.config/inkscape/extensions`
3. Restart Inkscape
4. Inkcut will be added to the Extensions menu
