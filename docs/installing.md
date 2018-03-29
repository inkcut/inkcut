### Install

See [original version](#original-version) for installing v1.0 on linux.

> There are no install packages for v2.0+ as it is an early release and is NOT
intended for end users. 

Developers can install all the dependencies and [build it from source](#building-from-source).

### Building from source

To build from source use the commands below. Using Python 3 is recommended.


#### Python 3 (Recommended)

```bash

virtualenv -p python3 venv
source venv activate

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
source venv activate

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

### Original version

To install on linux, simply extract the contents of the package into /home/your_username/.config/inkscape/extensions/

Before starting, ensure that the target machine has the required dependencies

```bash
pygtk and gtk
pyserial
librsvg2-common
```


Assuming the tar.gz archive is saved in your Downloads folder, you can use this command to install it. Replace inkcut-1.0.tar.gz with the archive name.

 ```bash
tar -xzvf Downloads/inkCut-1.0.tar.gz -C .config/inkscape/extensions/
```

Then restart all instances of inkscape.



### Running

Run `python main.py` (or `python3 main.py` depending on the system default) or to use the installed version simply run `inkcut`


