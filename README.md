# Inkcut

A an application for controlling 2D cnc machines

## Install

There are no install packages (yet). For now you can install 
all the dependencies and build it from source.


### Activate the virtual env

> Note: Using a virtual env is not required but highly recommended 
so these dependencies do not conflict with any other applications

On linux

```

#: From this folder
#: Or just 'virtualenv venv' for python 2
virtualenv -p python3 venv
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


pip install git+https://github.com/frmdstryr/enaml.git@latest
pip install git+https://github.com/frmdstryr/enamlx.git

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

## Running

Run `python main.py` or to use the installed version simply run `inkcut`

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



