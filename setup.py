#!/usr/bin/env python
from distutils.core import setup

setup(name='mutablerecord',
      description='recordset framework for small python structures',
      version='0.12',
      author='Alex Flint',
      author_email='alex.flint@gmail.com',
      url='https://github.com/alexflint/mutablerecord',
      packages=['mutablerecord'],
      package_dir={'mutablerecord': '.'},
      )
