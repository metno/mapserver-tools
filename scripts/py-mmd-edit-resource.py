#!/usr/bin/env python

import os
import sys
import uuid
import jinja2
import datetime
import rasterio
import xml.etree.ElementTree as et

mmd_file = sys.argv[1]
template_filename = sys.argv[2]
map_files_template_dir = sys.argv[3]
map_files_output_dir = sys.argv[4]
server_name = sys.argv[5]
mapserver_data_dir = sys.argv[6]
geotiff_files = sys.argv[7:]

server_data = '/data'


def get_geotiff_timestamp(geotiff_file):
    dataset = rasterio.open(geotiff_file)
    tags = dataset.tags()
    return dataset.profile['width'], dataset.profile['height'], datetime.datetime.strptime(tags['TIFFTAG_DATETIME'], '%Y:%m:%d %H:%M:%S')


width, height, geotiff_timestamp = get_geotiff_timestamp(geotiff_files[0])

layers = ['polar_overview', 'natural_with_night_fog']
ns = {'mmd': 'http://www.met.no/schema/mmd',
      'gml': 'http://www.opengis.net/gml'}


mi = uuid.uuid4()
mi = '444bd65b-1de7-4596-9b00-b998fc327ec7'
mi = '8505ad3e-f9e3-4de3-a080-8253443ac954'
map_output_file = 'mapserver-{}-{}.map'.format(mi, geotiff_timestamp.strftime('%Y%m%dT%H%M%SZ'))

env = jinja2.Environment(loader=jinja2.FileSystemLoader(map_files_template_dir))
t = env.get_template(template_filename)
data = {}
data['server_name'] = server_name
data['map_file_name'] = os.path.join(server_data, 'mapserver/map-files', map_output_file)
data['xsize'] = width
data['ysize'] = height
data['layers'] = []
layer = {}
layer['layer_name'] = "Overview"
layer['geotiff_filename'] = os.path.join(server_data, os.path.basename(geotiff_files[0]))
layer['layer_title'] = 'Overview'
layer['geotiff_timestamp'] = get_geotiff_timestamp(geotiff_files[0])[2].strftime('%Y-%m-%dT%H:%M:%SZ')

data['layers'].append(layer)

layer = {}
layer['layer_name'] = "NaturalWithNightFog"
layer['geotiff_filename'] = os.path.join(server_data, os.path.basename(geotiff_files[1]))
layer['layer_title'] = 'natural_with_night_fog'
layer['geotiff_timestamp'] = get_geotiff_timestamp(geotiff_files[1])[2].strftime('%Y-%m-%dT%H:%M:%SZ')
data['layers'].append(layer)

with open(os.path.join(map_files_output_dir, map_output_file), 'w') as fh:
    fh.write(t.render(data=data))

et.register_namespace('mmd', ns['mmd'])
et.register_namespace('gml', ns['gml'])
xtree = et.parse(mmd_file)
xroot = xtree.getroot()

for data_access in xroot.findall("mmd:data_access", ns):
    access_type = data_access.find("mmd:type", ns)
    if access_type.text == 'OGC WMS':
        xroot.remove(data_access)

# Manipulate uuid to make a test dataset
metadata_identifier = xroot.find("mmd:metadata_identifier", ns)
metadata_identifier.text = str(mi)


wms_data_access = et.SubElement(xroot, "mmd:data_access")
wms_data_access_type = et.SubElement(wms_data_access, "mmd:type")
wms_data_access_type.text = "OGC WMS"
wms_data_access_description = et.SubElement(wms_data_access, "mmd:description")
wms_data_access_description.text = "OGC Web Mapping Service, URI to GetCapabilities Document."
wms_data_access_resource = et.SubElement(wms_data_access, "mmd:resource")
get_capabilites = '&service=WMS&amp;version=1.3.0&amp;request=GetCapabilities'
wms_data_access_resource.text = "{}/cgi-bin/mapserv?map={}{}".format(server_name,
                                                                     os.path.join(server_data,
                                                                                  'mapserver/map-files',
                                                                                  map_output_file),
                                                                     get_capabilites)
wms_data_access_layers = et.SubElement(wms_data_access, 'mmd:wms_layers')
for layer in layers:
    wms_data_access_layer = et.SubElement(wms_data_access_layers, 'mmd:wms_layer')
    wms_data_access_layer.text = layer


xtree.write(os.path.basename(mmd_file), encoding='UTF-8')
