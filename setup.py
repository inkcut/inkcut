from setuptools import setup, find_packages

setup(
  name='inkcut',
  packages=find_packages('src'),
  package_dir={'':'./src'},
  install_requires=['enaml','twisted','enamlx'],
)
