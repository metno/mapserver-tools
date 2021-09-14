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
    input_data_files = ['testdata/overview_20210910_123318.tif', 'testdata/natural_with_night_fog_20210910_123318.tif']
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
