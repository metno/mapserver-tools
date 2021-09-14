"""Test py-mmd-edit-resource
"""

import pytest
import logging


def test_check_arguments():
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')
    cmd_args = None
    assert pmer.check_arguments(cmd_args) is True


def test_read_yaml_config_file():
    import sys
    from importlib import import_module

    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')
    yaml_config_file = 'etc/okd-satellite-layer-metadata.yaml'
    read_config = pmer.read_yaml_config_file(yaml_config_file)
    assert read_config == config
    read_config_debug = pmer.read_yaml_config_file(yaml_config_file, True)
    assert read_config_debug == config


def test_generate_render_data():
    """Test check if distribute."""
    import os
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}

    server_name = 'https://test.server.lo/'
    mapserver_data_dir = 'test_mapserver_data_dir'
    map_output_file = 'test_map_output_file'
    input_data_files = ['scripts/testdata/overview_20210910_123318.tif',
                        'scripts/testdata/natural_with_night_fog_20210910_123318.tif']
    data = pmer.generate_render_data(server_name, mapserver_data_dir, map_output_file, input_data_files, config)

    assert data['server_name'] == server_name
    assert data['map_file_name'] == 'test_mapserver_data_dir/mapserver/map-files/test_map_output_file'
    assert data['xsize'] == 2400
    assert data['ysize'] == 2750
    assert len(data['layers']) == 2
    for d_l, c_l, g_t in zip(data['layers'], config['layers'], input_data_files):
        assert d_l['layer_name'] == c_l['name']
        assert d_l['layer_title'] == c_l['title']
        assert d_l['geotiff_filename'] == os.path.join(mapserver_data_dir, os.path.basename(g_t))
        assert d_l['geotiff_timestamp'] == '2021-09-10T12:33:18Z'


def test_open_mmd_xml_file():
    import sys
    import xml
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'scripts/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    xtree = pmer.open_mmd_xml_file(input_mmd_xml_file, ns)
    assert isinstance(xtree, xml.etree.ElementTree.ElementTree) is True


def test_open_mmd_xml_file_fnf(capsys, mocker):
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'Non existing file'
    mocker.patch('xml.etree.ElementTree.parse', side_effect=FileNotFoundError, autoSpec=True)
    pmer.open_mmd_xml_file(input_mmd_xml_file, ns)
    captured = capsys.readouterr()
    assert 'Could not find the mmd xml input file. Please check you command line argument.' in captured.out
    capsys.disabled()


def test_get_metadata_indentifier_from_mmd_xml():
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'scripts/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    xtree = pmer.open_mmd_xml_file(input_mmd_xml_file, ns)

    mi = pmer.get_metadata_indentifier_from_mmd_xml(xtree, ns)
    assert mi == '4f0946c4-3a0b-42b8-9094-69287d16fa64'

    mi = '8505ad3e-f9e3-4de3-a080-8253443ac954'
    mi_reset = pmer.get_metadata_indentifier_from_mmd_xml(xtree, ns, mi)
    assert mi_reset == mi


def test_remove_wms_from_mmd_xml():
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'scripts/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    xroot = pmer.open_mmd_xml_file(input_mmd_xml_file, ns)
    xtree = xroot.getroot()
    pmer.remove_wms_from_mmd_xml(xtree, ns)
    for data_access in xroot.findall("mmd:data_access", ns):
        access_type = data_access.find("mmd:type", ns)
        assert access_type.text != 'OGC WMS'


def test_add_wms_to_mmd_xml():
    import os
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}
    server_name = 'https://test.server.lo/'
    mapserver_data_dir = 'test_mapserver_data_dir'
    map_output_file = 'test_map_output_file'
    input_data_files = ['scripts/testdata/overview_20210910_123318.tif',
                        'scripts/testdata/natural_with_night_fog_20210910_123318.tif']

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'scripts/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    xtree = pmer.open_mmd_xml_file(input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    pmer.remove_wms_from_mmd_xml(xroot, ns)
    pmer.add_wms_to_mmd_xml(xroot, server_name, mapserver_data_dir,
                            map_output_file, input_data_files, config)
    pmer.rewrite_mmd_xml(xtree, 'test-out.xml')

    xtree = pmer.open_mmd_xml_file('test-out.xml', ns)
    xroot = xtree.getroot()
    for data_access in xroot.findall("mmd:data_access", ns):
        access_type = data_access.find("mmd:type", ns)
        if access_type.text == 'OGC WMS':
            wms_data_access_description = data_access.find("mmd:description", ns)
            assert wms_data_access_description.text == "OGC Web Mapping Service, URI to GetCapabilities Document."
            wms_data_access_resource = data_access.find("mmd:resource", ns)
            s = ('https://test.server.lo//cgi-bin/mapserv?map=test_mapserver_data_dir/mapserver/map-files/'
                 'test_map_output_file&service=WMS&amp;version=1.3.0&amp;request=GetCapabilities')
            assert wms_data_access_resource.text == s
    os.remove('test-out.xml')       


def test_load_template():
    import sys
    import jinja2
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    map_template_file_name = 'map-file-template-okd-satellite.map'
    map_template_input_dir = 'templates/'
    template = pmer.load_template(map_template_input_dir, map_template_file_name)
    assert isinstance(template, jinja2.Template) is True
