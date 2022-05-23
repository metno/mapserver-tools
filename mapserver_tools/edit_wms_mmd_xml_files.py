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
import sys
import yaml
import jinja2
import datetime
import rasterio
import requests
import xml.etree.ElementTree as et


def match_input_file_with_layer_config(input_file, config):
    for layer in config['layers']:
        if os.path.basename(input_file).startswith(layer['match']):
            return layer
    print("Could not find matching layer config to the input file. Fix you layer config.")


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
                raise
    except FileNotFoundError:
        print("Could not find this config file. Please check the filename.")
    return config


class edit_wms_mmd_xml_files():
    def open_mmd_xml_file(self, input_mmd_xml_file, ns):
        xtree = None
        et.register_namespace('mmd', ns['mmd'])
        et.register_namespace('gml', ns['gml'])
        try:
            xtree = et.parse(input_mmd_xml_file)
        except FileNotFoundError:
            print("Could not find the mmd xml input file. Please check you command line argument.")
            # sys.exit(1)

        return xtree

    def remove_wms_from_mmd_xml(self, xroot, ns):
        for data_access in xroot.findall("mmd:data_access", ns):
            access_type = data_access.find("mmd:type", ns)
            if access_type.text == 'OGC WMS':
                xroot.remove(data_access)

    def get_metadata_indentifier_from_mmd_xml(self, xroot, ns, mi=None):
        # Manipulate uuid to make a test dataset
        metadata_identifier = xroot.find("mmd:metadata_identifier", ns)
        if mi:
            metadata_identifier.text = str(mi)

        return metadata_identifier.text

    def add_wms_to_mmd_xml(self, xroot, fast_api_netcdf_path, layers):
        wms_data_access = et.SubElement(xroot, "mmd:data_access")
        wms_data_access_type = et.SubElement(wms_data_access, "mmd:type")
        wms_data_access_type.text = "OGC WMS"
        wms_data_access_description = et.SubElement(wms_data_access, "mmd:description")
        wms_data_access_description.text = "OGC Web Mapping Service, URI to GetCapabilities Document."
        wms_data_access_resource = et.SubElement(wms_data_access, "mmd:resource")
        get_capabilites = 'service=WMS&version=1.3.0&request=GetCapabilities'
        wms_data_access_resource.text = f"{fast_api_netcdf_path}?{get_capabilites}"
        wms_data_access_layers = et.SubElement(wms_data_access, 'mmd:wms_layers')

        for layer in layers:
            wms_data_access_layer = et.SubElement(wms_data_access_layers, 'mmd:wms_layer')
            wms_data_access_layer.text = layer

    def add_wms_to_mmd_xml_old(self, xroot, server_name, mapserver_data_dir, map_output_file, input_data_files, config):
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

    def rewrite_mmd_xml(self, xtree, input_mmd_xml_file):
        xtree.write(input_mmd_xml_file, encoding='UTF-8')

    def read_layers_from_getcapabilities(self, resource):
        "Read and parse layer names from getcapabilities document"

        gcd = requests.get(resource).text
        xtree = et.fromstring(gcd)
        layers = []
        for layer in xtree.findall(".//{http://www.opengis.net/wms}Capability/{http://www.opengis.net/wms}Layer/"
                                   "{http://www.opengis.net/wms}Layer/{http://www.opengis.net/wms}Name"):
            layers.append(layer.text)
        return layers

    def generate_uri(self, mmd_xml_file):
        bn, _ = os.path.splitext(os.path.basename(mmd_xml_file))
        basename = bn.split('-')
        start_time = datetime.datetime.strptime(basename[-2], '%Y%m%d%H%M%S')
        netcdf_path = f'satellite-thredds/polar-swath/{start_time:%Y/%m/%d}/{bn}.nc'
        return bn, netcdf_path


class generate_mapserver_map_file():
    def get_geotiff_timestamp(self, geotiff_file):
        dataset = rasterio.open(geotiff_file)
        tags = dataset.tags()
        return dataset.profile['width'], dataset.profile['height'], datetime.datetime.strptime(tags['TIFFTAG_DATETIME'],
                                                                                               '%Y:%m:%d %H:%M:%S')

    def generate_render_data(self, server_name, mapserver_data_dir, map_output_file, input_data_files, config):
        data = {}
        data['server_name'] = server_name
        data['map_file_name'] = os.path.join(mapserver_data_dir, 'mapserver/map-files', map_output_file)
        # Assume width and height from the first geotiff file and the following the same
        width, height, _ = self.get_geotiff_timestamp(input_data_files[0])
        data['xsize'] = width
        data['ysize'] = height
        data['layers'] = []
        for file_layer in input_data_files:
            layer = {}
            layer_config = match_input_file_with_layer_config(file_layer, config)
            layer['layer_name'] = layer_config['name']
            layer['geotiff_filename'] = os.path.join(mapserver_data_dir, os.path.basename(file_layer))
            layer['layer_title'] = layer_config['title']
            layer['geotiff_timestamp'] = self.get_geotiff_timestamp(file_layer)[2].strftime('%Y-%m-%dT%H:%M:%SZ')

            data['layers'].append(layer)
        return data

    def load_template(self, map_template_input_dir, map_template_file_name):
        try:
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(map_template_input_dir))
        except TypeError:
            print("Could not find map template input dir. Please check this directory.")
            return None

        try:
            t = env.get_template(map_template_file_name)
        except jinja2.exceptions.TemplateNotFound:
            print("Could not find the template. Please check the filename.")
            return None
        return t

    def write_map_file(self, map_file_output_dir, map_output_file, template, data):
        with open(os.path.join(map_file_output_dir, map_output_file), 'w') as fh:
            fh.write(template.render(data=data))


def main():  # pragma: no cover
    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}
    ewmxf = edit_wms_mmd_xml_files()
    mmd_xml_file = ''
    try:
        mmd_xml_file = sys.argv[1]
    except IndexError:
        pass
    fast_api = 'https://fastapi-dev.s-enda.k8s.met.no/api/get_mapserv'
    try:
        fast_api = sys.argv[2]
    except IndexError:
        pass
    bn, netcdf_path = ewmxf.generate_uri(mmd_xml_file)
    xtree = ewmxf.open_mmd_xml_file(mmd_xml_file, ns)
    xroot = xtree.getroot()
    ewmxf.remove_wms_from_mmd_xml(xroot, ns)
    layers_dict = {'iband': ['hr_overview', 'ir_window_channel'],
                   'dnb': ['adaptive_dnb']}
    layers = ['overview', 'ir_window_channel']
    for layer in layers_dict:
        if layer in bn:
            layers = layers_dict[layer]
            break
    ewmxf.add_wms_to_mmd_xml(xroot, os.path.join(fast_api, netcdf_path), layers)
    ewmxf.rewrite_mmd_xml(xtree, f'../{mmd_xml_file}')


if __name__ == '__main__':  # pragma: no cover
    main()
