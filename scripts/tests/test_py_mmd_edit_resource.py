"""Test py-mmd-edit-resource
"""

import pytest
import logging


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
