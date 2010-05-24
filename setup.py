#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from distribute_setup import use_setuptools; use_setuptools()
from setuptools import setup, find_packages


rel_file = lambda *args: os.path.join(os.path.dirname(os.path.abspath(__file__)), *args)

def read_from(filename):
    fp = open(filename)
    try:
        return fp.read()
    finally:
        fp.close()

def get_version():
    data = read_from(rel_file('src', 'djclsview.py'))
    return re.search(r"__version__ = '([^']+)'", data).group(1)


setup(
    name             = 'django-clsview',
    version          = get_version(),
    author           = "Zachary Voase",
    author_email     = "z@zacharyvoase.com",
    url              = 'http://github.com/zacharyvoase/django-clsview',
    description      = "Yet another class-based view system for Django.",
    py_modules       = ['djclsview'],
    package_dir      = {'': 'src'},
)
