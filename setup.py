from setuptools import setup, find_packages

setup(
    name='inkcut',
    packages=find_packages(),
    version="2.0.1",
    author="CodeLV",
    author_email="frmdstryr@gmail.com",
    license='GPLv3',
    url='https://github.com/codelv/inkcut/',
    description="An application for controlling 2D plotters, cutters, "
                "engravers, and CNC machines.",
    long_description=open("README.md").read(),
    entry_points={
        'console_scripts': ['inkcut = inkcut.main'],
    },
    install_requires=[
        'enaml', # must install pyqt or pyside
        'twisted',
        'enamlx', # use pip install  git+https://github.com/frmdstry/enamlx.git
        'pyqtgraph',
        'qt4reactor',
        'qtconsole',
        'pyserial',
        'faulthandler',
        'jsonpickle',
        'lxml', # use sudo apt install libxml2-dev libxslt-dev
    ],
)
