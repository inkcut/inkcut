# Inkcut

A an application for controlling 2D cnc machines

## Install

See setup.py

### Raspberry pi


### Activate the virtual env

```bash
source ~/.profile           #" loads virtual environment profile settings
workon cv                   #" opens virtual environment cv
python                      #" open python
>>> import cv2              #" cv2 is the opencv library
>>> cv2.funstuff            #" execute cv2 stuff

```

### Install everything in the setup file

```bash

pip install enaml
pip install twisted
pip install git+https://github.com/frmdstryr/enamlx.git
pip install pyqtgraph
pip install jsonpickle

# Install lxml
sudo apt install libxml2-dev libxslt-dev
pip install lxml

# Install pyqt4
sudo apt install python-qt4
ln -s /usr/lib/python2.7/dist-packages/PyQt4/ ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/sip.so ~/.virtualenvs/cv/lib/python2.7/site-packages/


# Install RPI.GPIO
pip install RPi.GPIO

# Install zbar
sudo apt-get install libzbar-dev
pip install zbar


```

## Running

Run `python main.py`

## How it all works

For now... open `inkcut/workbench/ui/plugin.py`
and import and create an instance of your device in the `_default_device` method.

Your device should be a subclass of 
[inkcut.workbench.core.device.Device](https://gitlab.com/frmdstryr/inkcut/tree/master/src/inkcut/workbench/core/device.py)). 
All the crap is in there and 
[inkcut.workbench.core.job.Job](https://gitlab.com/frmdstryr/inkcut/tree/master/src/inkcut/workbench/core/job.py).

It calls your code in 
[inkcut.plugins.jeffy.jeffy.JeffyDevice](https://gitlab.com/frmdstryr/inkcut/tree/master/src/inkcut/plugins/jeffy/jeffy.py).
where you can do whatever you want.


### How to use markdown

[Markdown](https://guides.github.com/features/mastering-markdown/)


### Pushing crap with git

Cd to the folder and

```bash

git add <file/path>
git commit -m "Some message"
git push origin master

#: Config is in .git/config

```



