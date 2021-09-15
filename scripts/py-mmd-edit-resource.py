#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2021

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

import sys
import uuid
import argparse

from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file
from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
from mapserver_tools.edit_wms_mmd_xml_files import read_yaml_config_file, check_arguments

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config-file",
                        help="Yaml config file to map the various input data files to the neccessary metadata in the "
                             "mapserver map file.")
    parser.add_argument("-m", "--input-mmd-xml-file",
                        help="The mmd xml file to be edited.")
    parser.add_argument("-t", "--map-template-file-name",
                        help="The map template file to be used.")
    parser.add_argument("-i", "--map-template-input-dir",
                        help="The input directory of the map template")
    parser.add_argument("-o", "--map-file-output-dir",
                        help="Directory where to store the rendered map file")
    parser.add_argument("-s", "--server-name",
                        help="Hostname of the mapserver service, eg: https://s-enda-ogc-dev.k8s.met.no/")
    parser.add_argument("-d", "--mapserver-data-dir",
                        help="The kubernetes volume mount to the data itself, ie. geotiff and map file.")
    parser.add_argument("-g", "--input-data-files",
                        nargs='*',
                        help="Input data file(s). Each file will have it's own layer in the generated map file. "
                             "The input data assumed to be geotiff.")

    cmd_args = parser.parse_args()

    if not check_arguments(cmd_args):
        print("Failed to find mandatory arguments. Please check your arguments and try again.")
        parser.print_help()
        sys.exit(1)

    config = read_yaml_config_file(cmd_args.config_file)

    gmmf = generate_mapserver_map_file()
    ewmxf = edit_wms_mmd_xml_files()

    width, height, geotiff_timestamp = gmmf.get_geotiff_timestamp(cmd_args.input_data_files[0])
    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    xtree = ewmxf.open_mmd_xml_file(cmd_args.input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    ewmxf.remove_wms_from_mmd_xml(xroot, ns)

    mi = uuid.uuid4()
    mi = '444bd65b-1de7-4596-9b00-b998fc327ec7'
    mi = '8505ad3e-f9e3-4de3-a080-8253443ac954'
    mi = ewmxf.get_metadata_indentifier_from_mmd_xml(xroot, ns, mi)

    map_output_file = 'mapserver-{}-{}.map'.format(mi, geotiff_timestamp.strftime('%Y%m%dT%H%M%SZ'))

    ewmxf.add_wms_to_mmd_xml(xroot, cmd_args.server_name, cmd_args.mapserver_data_dir,
                             map_output_file, cmd_args.input_data_files, config)
    ewmxf.rewrite_mmd_xml(xtree, cmd_args.input_mmd_xml_file)

    data = gmmf.generate_render_data(cmd_args.server_name, cmd_args.mapserver_data_dir,
                                     map_output_file, cmd_args.input_data_files, config)

    template = gmmf.load_template(cmd_args.map_template_input_dir, cmd_args.map_template_file_name)

    gmmf.write_map_file(cmd_args.map_file_output_dir, map_output_file, template, data)
