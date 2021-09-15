"""Test py-mmd-edit-resource
"""

import pytest
import logging


def test_generate_render_data():
    """Test check if distribute."""
    import sys
    from importlib import import_module

    sys.path.append('./scripts')
    pmer = import_module('py-mmd-edit-resource')

    server_name = 'https://test.server.lo/'
    mapserver_data_dir = 'test_mapserver_data_dir'
    map_output_file = 'test_map_output_file'
    input_data_files = ['overview_20210910_123318.tif', 'natural_with_night_fog_20210910_123318.tif']
    data = pmer.generate_render_data(server_name, mapserver_data_dir, map_output_file, input_data_files)

    print(data)
