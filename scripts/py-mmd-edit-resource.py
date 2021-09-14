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

import os
import re
import sys
import uuid
import yaml
import jinja2
import argparse
import datetime
import rasterio
import xml.etree.ElementTree as et


def check_arguments(cmd_args):
    return True


def read_yaml_config_file(yaml_config_file, debug=False):
    config = None
    try:
        with open(yaml_config_file, 'r') as stream:
            try:
                config = yaml.load(stream, Loader=yaml.FullLoader)
                if debug:
                    import pprint
                    pp = pprint.PrettyPrinter(indent=4)
                    pp.pprint(config)
            except yaml.YAMLError as exc:
                print("Failed reading yaml config file: {} with: {}".format(yaml_config_file, exc))
                raise yaml.YAMLError
    except FileNotFoundError:
        print("Could not find this config file. Please check the filename.")
        sys.exit(1)
    return config


def get_geotiff_timestamp(geotiff_file):
    dataset = rasterio.open(geotiff_file)
    tags = dataset.tags()
    return dataset.profile['width'], dataset.profile['height'], datetime.datetime.strptime(tags['TIFFTAG_DATETIME'],
                                                                                           '%Y:%m:%d %H:%M:%S')


def match_input_file_with_layer_config(input_file, config):
    for layer in config['layers']:
        if os.path.basename(input_file).startswith(layer['match']):
            return layer
    print("Could not find matching layer config to the input file. Fix you layuer config.")
    sys.exit(1)


def generate_render_data(server_name, mapserver_data_dir, map_output_file, input_data_files, config):
    data = {}
    data['server_name'] = server_name
    data['map_file_name'] = os.path.join(mapserver_data_dir, 'mapserver/map-files', map_output_file)
    # Assume width and height from the first geotiff file and the following the same
    width, height, _ = get_geotiff_timestamp(input_data_files[0])
    data['xsize'] = width
    data['ysize'] = height
    data['layers'] = []
    for file_layer in input_data_files:
        layer = {}
        layer_config = match_input_file_with_layer_config(file_layer, config)
        layer['layer_name'] = layer_config['name']
        layer['geotiff_filename'] = os.path.join(mapserver_data_dir, os.path.basename(file_layer))
        layer['layer_title'] = layer_config['title']
        layer['geotiff_timestamp'] = get_geotiff_timestamp(file_layer)[2].strftime('%Y-%m-%dT%H:%M:%SZ')

        data['layers'].append(layer)
    return data


def open_mmd_xml_file(input_mmd_xml_file, ns):
    xtree = None
    et.register_namespace('mmd', ns['mmd'])
    et.register_namespace('gml', ns['gml'])
    try:
        xtree = et.parse(input_mmd_xml_file)
    except FileNotFoundError:
        print("Could not find the mmd xml input file. Please check you command line argument.")
        # sys.exit(1)

    return xtree


def remove_wms_from_mmd_xml(xroot, ns):
    for data_access in xroot.findall("mmd:data_access", ns):
        access_type = data_access.find("mmd:type", ns)
        if access_type.text == 'OGC WMS':
            xroot.remove(data_access)


def get_metadata_indentifier_from_mmd_xml(xroot, ns, mi=None):
    # Manipulate uuid to make a test dataset
    metadata_identifier = xroot.find("mmd:metadata_identifier", ns)
    if mi:
        metadata_identifier.text = str(mi)

    return metadata_identifier.text


def add_wms_to_mmd_xml(xroot, server_name, mapserver_data_dir, map_output_file, input_data_files, config):
    wms_data_access = et.SubElement(xroot, "mmd:data_access")
    wms_data_access_type = et.SubElement(wms_data_access, "mmd:type")
    wms_data_access_type.text = "OGC WMS"
    wms_data_access_description = et.SubElement(wms_data_access, "mmd:description")
    wms_data_access_description.text = "OGC Web Mapping Service, URI to GetCapabilities Document."
    wms_data_access_resource = et.SubElement(wms_data_access, "mmd:resource")
    get_capabilites = '&service=WMS&amp;version=1.3.0&amp;request=GetCapabilities'
    wms_data_access_resource.text = "{}/cgi-bin/mapserv?map={}{}".format(server_name,
                                                                         os.path.join(mapserver_data_dir,
                                                                                      'mapserver/map-files',
                                                                                      map_output_file),
                                                                         get_capabilites)
    wms_data_access_layers = et.SubElement(wms_data_access, 'mmd:wms_layers')

    for file_layer in input_data_files:
        layer_config = match_input_file_with_layer_config(file_layer, config)
        wms_data_access_layer = et.SubElement(wms_data_access_layers, 'mmd:wms_layer')
        wms_data_access_layer.text = layer_config['name']


def rewrite_mmd_xml(xtree, input_mmd_xml_file):
    xtree.write(os.path.basename(input_mmd_xml_file), encoding='UTF-8')


def load_template(map_template_input_dir, map_template_file_name):
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(map_template_input_dir))
    except TypeError:
        print("Could not find map template input dir. Please check this directory.")
        sys.exit(1)

    try:
        t = env.get_template(map_template_file_name)
    except jinja2.exceptions.TemplateNotFound:
        print("Could not find the template. Please check the filename.")
        sys.exit(1)

    return t


def write_map_file(map_file_output_dir, map_output_file, template, data):
    with open(os.path.join(map_file_output_dir, map_output_file), 'w') as fh:
        fh.write(template.render(data=data))


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

    width, height, geotiff_timestamp = get_geotiff_timestamp(cmd_args.input_data_files[0])
    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    xtree = open_mmd_xml_file(cmd_args.input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    remove_wms_from_mmd_xml(xroot, ns)

    mi = uuid.uuid4()
    mi = '444bd65b-1de7-4596-9b00-b998fc327ec7'
    mi = '8505ad3e-f9e3-4de3-a080-8253443ac954'
    mi = get_metadata_indentifier_from_mmd_xml(xroot, ns, mi)

    map_output_file = 'mapserver-{}-{}.map'.format(mi, geotiff_timestamp.strftime('%Y%m%dT%H%M%SZ'))

    add_wms_to_mmd_xml(xroot, cmd_args.server_name, cmd_args.mapserver_data_dir,
                       map_output_file, cmd_args.input_data_files, config)
    rewrite_mmd_xml(xtree, cmd_args.input_mmd_xml_file)

    data = generate_render_data(cmd_args.server_name, cmd_args.mapserver_data_dir,
                                map_output_file, cmd_args.input_data_files, config)

    template = load_template(cmd_args.map_template_input_dir, cmd_args.map_template_file_name)

    write_map_file(cmd_args.map_file_output_dir, map_output_file, template, data)
