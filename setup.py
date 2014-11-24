#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup
import os.path
import re

init_file = os.path.dirname(__file__)
init_file = os.path.abspath(init_file)
init_file = os.path.join(init_file, 'thisj', '__init__.py')
with open(init_file, 'r') as fp:
    try:
        version = re.findall(r"^__version__\s*=\s*'([^']+)'$", fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

setup(name='thisj',
    version=version,
    description='Python web framework, base on aiohttp',
    author='Samuel Zhou',
    author_email='thisissc@gmail.com',
    url='https://code.google.com/p/thisj/',
    packages=['thisj'],
)

