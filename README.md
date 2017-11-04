# Inkcut

A an application for controlling 2D cnc machines

## Install

See setup.py

### Raspberry pi


### Activate the virtual env

```bash
source ~/.profile           " loads virtual environment profile settings
workon cv                   " opens virtual environment cv
python                      " open python
>>> import cv2              " cv2 is the opencv library
>>> cv2.funstuff            " execute cv2 stuff

```

### Install everything in the setup file

```bash

pip install enaml
pip install twisted
pip install git+https://github.com/frmdstry/enamlx.git
pip install pyqtgraph
pip install jsonpickle

# Install lxml
sudo apt install libxml2-dev libxslt-dev
pip install lxml

# Install pyqt4
sudo apt install python-pyqt4
ln -s /usr/lib/python2.7/dist-packages/PyQt4/ ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/sip.so ~/.virtualenvs/cv/lib/python2.7/site-packages/


```

