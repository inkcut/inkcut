# Inkcut

A an application for controlling 2D cnc machines

## Install

There are no install packages (yet). For now you can install 
all the dependencies and build it from source.


### Activate the virtual env

On linux

```

#: From this folder
virtualenv venv
source venv activate


```


On the raspberry pi

```bash
source ~/.profile           #" loads virtual environment profile settings
workon cv                   #" opens virtual environment cv
python                      #" open python
>>> import cv2              #" cv2 is the opencv library
>>> cv2.funstuff            #" execute cv2 stuff

```

Now install the dependencies

### Install everything in the setup file

```bash

pip install git+https://github.com/nucleic/enaml.git
pip install twisted
pip install git+https://github.com/frmdstryr/enamlx.git
pip install pyqtgraph
pip install jsonpickle
pip install qt4reactor

# Install lxml
sudo apt install libxml2-dev libxslt-dev
pip install lxml

# Install pyqt4
sudo apt install python-qt4

#: Replace ~/.virtualenvs/cv with venv/ on linux
ln -s /usr/lib/python2.7/dist-packages/PyQt4/ ~/.virtualenvs/cv/lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/sip.so ~/.virtualenvs/cv/lib/python2.7/site-packages/

# Install qtconsole
pip install qtconsole

# Install faulthandler
pip install faulthandler

# Install pyserial 
pip install pyserial

# Install RPI.GPIO (pi only)
pip install RPi.GPIO

# Install zbar (pi only)
pip install git+https://github.com/npinchot/zbar.git


```

## Running

Run `python main.py`

## Docs

Docs coming soon...


### How to use markdown

[Markdown](https://guides.github.com/features/mastering-markdown/)


### Pushing changes with git

Cd to the folder and

```bash

git add <file/path>
git commit -m "Some message"
git push origin master

#: Config is in .git/config

```



