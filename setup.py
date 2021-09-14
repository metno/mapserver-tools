#!/usr/bin/python
# Copyright (c) 2021.
#

# Author(s):
#   Trygve Aspenes <trygveas@met.no>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""Setup for mapserver tools
"""

from setuptools import setup

setup(name="mapserver-tools",
      version="0.1.0",
      description='mapserver tools',
      author='Trygve Aspenes',
      author_email='trygveas@met.no',
      classifiers=["Development Status :: 4 - Beta",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 "
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="git@gitlab.met.no:s-enda/mapserver-tools.git",
      scripts=['scripts/py-mmd-edit-resource.py'],
      data_files=[],
      packages=[],
      zip_safe=False,
      install_requires=['jinja2', 'rasterio'])
