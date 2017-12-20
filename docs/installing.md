### Install


See [original version](#original-version) for installing v1.0.

There are no install packages (yet). For now you can install 
all the dependencies and build it from source.

> This is an early release and is NOT intended for end users. 
 


#### Virtual environment

Using a virtual env is not required but highly recommended 
so these dependencies do not conflict with any other applications

On linux


    :::bash
    #: From this folder, or just 'virtualenv venv' for python 2
    virtualenv -p python3 venv
    source venv activate



On the raspberry pi

    :::bash
    source ~/.profile           #" loads virtual environment profile settings
    workon cv                   #" opens virtual environment cv
    python                      #" open python
    >>> import cv2              #" cv2 is the opencv library
    >>> cv2.funstuff            #" execute cv2 stuff



#### Install dependencies

Now install the dependencies

        :::bash
        
        
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




### Running

Run `python main.py` or to use the installed version simply run `inkcut`

### Original version

To install on linux, simply extract the contents of the package into /home/your_username/.config/inkscape/extensions/

Before starting, ensure that the target machine has the required dependencies

    :::bash
    pygtk and gtk
    pyserial
    librsvg2-common


Assuming the tar.gz archive is saved in your Downloads folder, you can use this command to install it. Replace inkcut-1.0.tar.gz with the archive name.

    :::bash
    tar -xzvf Downloads/inkCut-1.0.tar.gz -C .config/inkscape/extensions/

Then restart all instances of inkscape.


