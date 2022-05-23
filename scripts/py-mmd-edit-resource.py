#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021, 2022

# Author(s):

#   Trygve Aspenes

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import argparse

from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
from mapserver_tools.edit_wms_mmd_xml_files import check_arguments

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--input-mmd-xml-file",
                        help="The mmd xml file to be edited.")
    parser.add_argument("-s", "--server-name",
                        help="Hostname of the fastapi service, eg: https://s-enda-ogc-dev.k8s.met.no/")

    cmd_args = parser.parse_args()

    if not check_arguments(cmd_args):
        print("Failed to find mandatory arguments. Please check your arguments and try again.")
        parser.print_help()
        sys.exit(1)

    ewmxf = edit_wms_mmd_xml_files()

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    bn, netcdf_path = ewmxf.generate_uri(cmd_args.input_mmd_xml_file)
    xtree = ewmxf.open_mmd_xml_file(cmd_args.input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    ewmxf.remove_wms_from_mmd_xml(xroot, ns)
    layers_dict = {'iband': ['hr_overview', 'ir_window_channel'],
                   'dnb': ['adaptive_dnb']}
    layers = ['overview', 'ir_window_channel']
    for layer in layers_dict:
        if layer in bn:
            layers = layers_dict[layer]
            break

    ewmxf.add_wms_to_mmd_xml(xroot, os.path.join(cmd_args.server_name, netcdf_path), layers)
    ewmxf.rewrite_mmd_xml(xtree, cmd_args.input_mmd_xml_file)
