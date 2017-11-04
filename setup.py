from setuptools import setup, find_packages

setup(
  name='inkcut',
  packages=find_packages('src'),
  package_dir={'':'./src'},
  entry_points={
	'console_scripts':['inkcut = inkcut.main:main'],
  },
  install_requires=[
	'enaml', # must install pyqt or pyside
	'twisted',
	'enamlx', # use pip install  git+https://github.com/frmdstry/enamlx.git
        'pyqtgraph',
	'jsonpickle',
	'lxml', # use sudo apt install libxml2-dev libxslt-dev
  ],
)
