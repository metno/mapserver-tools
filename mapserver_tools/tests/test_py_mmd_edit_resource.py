"""Test py-mmd-edit-resource
"""

import pytest


def test_check_arguments():
    from mapserver_tools.edit_wms_mmd_xml_files import check_arguments
    cmd_args = None
    assert check_arguments(cmd_args) is True


def test_read_yaml_config_file():
    from mapserver_tools.edit_wms_mmd_xml_files import read_yaml_config_file
    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}

    yaml_config_file = 'etc/okd-satellite-layer-metadata.yaml'
    read_config = read_yaml_config_file(yaml_config_file)
    assert read_config == config
    read_config_debug = read_yaml_config_file(yaml_config_file, True)
    assert read_config_debug == config


def test_read_yaml_config_file_exception1(mocker):
    import yaml
    from mapserver_tools.edit_wms_mmd_xml_files import read_yaml_config_file
    yaml_config_file = 'etc/okd-satellite-layer-metadata.yaml'
    mocker.patch('yaml.load', side_effect=yaml.YAMLError)

    with pytest.raises(yaml.YAMLError):
        read_yaml_config_file(yaml_config_file)


def test_read_yaml_config_file_exception2(capsys, mocker):
    from mapserver_tools.edit_wms_mmd_xml_files import read_yaml_config_file
    yaml_config_file = 'etc/okd-satellite-layer-metadata.yaml'
    mocker.patch('builtins.open', side_effect=FileNotFoundError)

    read_yaml_config_file(yaml_config_file)
    captured = capsys.readouterr()
    assert 'Could not find this config file. Please check the filename.' in captured.out
    capsys.disabled()


def test_generate_render_data():
    """Test check if distribute."""
    import os
    from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file

    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}

    server_name = 'https://test.server.lo/'
    mapserver_data_dir = 'test_mapserver_data_dir'
    map_output_file = 'test_map_output_file'
    input_data_files = ['mapserver_tools/tests/testdata/overview_20210910_123318.tif',
                        'mapserver_tools/tests/testdata/natural_with_night_fog_20210910_123318.tif']
    gmmf = generate_mapserver_map_file()
    data = gmmf.generate_render_data(server_name, mapserver_data_dir, map_output_file, input_data_files, config)

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
    import xml
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ewmxf = edit_wms_mmd_xml_files()
    xtree = ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)
    assert isinstance(xtree, xml.etree.ElementTree.ElementTree) is True


def test_open_mmd_xml_file_fnf(capsys, mocker):
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'Non existing file'
    mocker.patch('xml.etree.ElementTree.parse', side_effect=FileNotFoundError, autoSpec=True)
    ewmxf = edit_wms_mmd_xml_files()
    ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)
    captured = capsys.readouterr()
    assert 'Could not find the mmd xml input file. Please check you command line argument.' in captured.out
    capsys.disabled()


def test_get_metadata_indentifier_from_mmd_xml():
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ewmxf = edit_wms_mmd_xml_files()
    xtree = ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)

    mi = ewmxf.get_metadata_indentifier_from_mmd_xml(xtree, ns)
    assert mi == '4f0946c4-3a0b-42b8-9094-69287d16fa64'

    mi = '8505ad3e-f9e3-4de3-a080-8253443ac954'
    mi_reset = ewmxf.get_metadata_indentifier_from_mmd_xml(xtree, ns, mi)
    assert mi_reset == mi


def test_remove_wms_from_mmd_xml():
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ewmxf = edit_wms_mmd_xml_files()
    xroot = ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)
    xtree = xroot.getroot()
    ewmxf.remove_wms_from_mmd_xml(xtree, ns)
    for data_access in xroot.findall("mmd:data_access", ns):
        access_type = data_access.find("mmd:type", ns)
        assert access_type.text != 'OGC WMS'


def test_add_wms_to_mmd_xml_old():
    import os
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files

    config = {'layers': [{'match': 'overview',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}
    server_name = 'https://test.server.lo/'
    mapserver_data_dir = 'test_mapserver_data_dir'
    map_output_file = 'test_map_output_file'
    input_data_files = ['mapserver_tools/tests/testdata/overview_20210910_123318.tif',
                        'mapserver_tools/tests/testdata/natural_with_night_fog_20210910_123318.tif']

    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}

    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ewmxf = edit_wms_mmd_xml_files()
    xtree = ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    ewmxf.remove_wms_from_mmd_xml(xroot, ns)
    ewmxf.add_wms_to_mmd_xml_old(xroot, server_name, mapserver_data_dir,
                                 map_output_file, input_data_files, config)
    ewmxf.rewrite_mmd_xml(xtree, 'test-out.xml')

    xtree = ewmxf.open_mmd_xml_file('test-out.xml', ns)
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

def test_add_wms_to_mmd_xml():
    import os
    import datetime
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ns = {'mmd': 'http://www.met.no/schema/mmd',
          'gml': 'http://www.opengis.net/gml'}
    fast_api = 'https://fastapi-dev.s-enda.k8s.met.no/api/get_mapserv'
    bn, _ = os.path.splitext(os.path.basename(input_mmd_xml_file))
    basename = bn.split('-')
    start_time = datetime.datetime.strptime(basename[-2], '%Y%m%d%H%M%S')
    netcdf_path = f'satellite-thredds/polar-swath/{start_time:%Y/%m/%d}/{bn}.nc'
    fast_api_netcdf_path = os.path.join(fast_api, netcdf_path)
    ewmxf = edit_wms_mmd_xml_files()
    xtree = ewmxf.open_mmd_xml_file(input_mmd_xml_file, ns)
    xroot = xtree.getroot()
    ewmxf.remove_wms_from_mmd_xml(xroot, ns)
    layers = ['overview', 'ir_window_channel']
    ewmxf.add_wms_to_mmd_xml(xroot, fast_api_netcdf_path, layers)
    ewmxf.rewrite_mmd_xml(xtree, 'test-out.xml')

    # Do the checks
    xtree = ewmxf.open_mmd_xml_file('test-out.xml', ns)
    xroot = xtree.getroot()
    for data_access in xroot.findall("mmd:data_access", ns):
        access_type = data_access.find("mmd:type", ns)
        if access_type.text == 'OGC WMS':
            wms_data_access_description = data_access.find("mmd:description", ns)
            assert wms_data_access_description.text == "OGC Web Mapping Service, URI to GetCapabilities Document."
            wms_data_access_resource = data_access.find("mmd:resource", ns)
            s = ('https://fastapi-dev.s-enda.k8s.met.no/api/get_mapserv/satellite-thredds/polar-swath/'
                 '2021/09/01/noaa19-avhrr-20210901070230-20210901071648.nc?'
                 'service=WMS&version=1.3.0&request=GetCapabilities')
            assert wms_data_access_resource.text == s

    os.remove('test-out.xml')


def test_generate_uri():
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
    input_mmd_xml_file = 'mapserver_tools/tests/testdata/noaa19-avhrr-20210901070230-20210901071648.xml'
    ewmxf = edit_wms_mmd_xml_files()
    bn, netcdf_path = ewmxf.generate_uri(input_mmd_xml_file)
    assert bn == 'noaa19-avhrr-20210901070230-20210901071648'
    assert netcdf_path == 'satellite-thredds/polar-swath/2021/09/01/noaa19-avhrr-20210901070230-20210901071648.nc'


def test_load_template():
    import jinja2
    from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file

    map_template_file_name = 'map-file-template-okd-satellite.map'
    map_template_input_dir = 'templates/'
    gmmf = generate_mapserver_map_file()
    template = gmmf.load_template(map_template_input_dir, map_template_file_name)
    assert isinstance(template, jinja2.Template) is True


def test_load_template_exception1(mocker, capsys):
    from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file

    map_template_file_name = 'map-file-template-okd-satellite.map'
    map_template_input_dir = 'templates/'
    mocker.patch('jinja2.Environment', side_effect=TypeError)
    gmmf = generate_mapserver_map_file()
    gmmf.load_template(map_template_input_dir, map_template_file_name)
    captured = capsys.readouterr()
    assert 'Could not find map template input dir. Please check this directory.' in captured.out
    capsys.disabled()


def test_load_template_exception2(capsys):
    from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file

    map_template_file_name = 'TEST-map-file-template-okd-satellite.map'
    map_template_input_dir = 'templates/'
    gmmf = generate_mapserver_map_file()
    gmmf.load_template(map_template_input_dir, map_template_file_name)
    captured = capsys.readouterr()
    assert 'Could not find the template. Please check the filename.' in captured.out
    capsys.disabled()


def test_match_input_file_with_layer_config(capsys):
    from mapserver_tools.edit_wms_mmd_xml_files import match_input_file_with_layer_config
    config = {'layers': [{'match': 'TEST',
                          'name': 'Overview',
                          'title': 'Overview'},
                         {'match': 'natural_with_night_fog',
                          'name': 'natural_with_night_fog',
                          'title': 'Natural with night fog'}]}
    input_data_file = 'mapserver_tools/tests/testdata/overview_20210910_123318.tif'
    match_input_file_with_layer_config(input_data_file, config)
    captured = capsys.readouterr()
    assert 'Could not find matching layer config to the input file. Fix you layer config.' in captured.out
    capsys.disabled()


def test_write_map_file():
    import os
    from mapserver_tools.edit_wms_mmd_xml_files import generate_mapserver_map_file
    gmmf = generate_mapserver_map_file()
    map_file_output_dir = '.'
    map_output_file = 'TEST.map'
    data = {}
    map_template_file_name = 'map-file-template-okd-satellite.map'
    map_template_input_dir = 'templates/'
    template = gmmf.load_template(map_template_input_dir, map_template_file_name)

    gmmf.write_map_file(map_file_output_dir, map_output_file, template, data)
    assert os.path.exists(os.path.join(map_file_output_dir, map_output_file)) is True
    os.remove(os.path.join(map_file_output_dir, map_output_file))


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, text_data, status_code):
            self.text = text_data
            self.status_code = status_code

    with open("mapserver_tools/tests/testdata/getcapabilities.xml", 'r') as f:
        getcapabilitites_test = f.read()
    if args[0] == 'https://some-host/?request=getcapabilities':
        return MockResponse(getcapabilitites_test, 200)


def test_read_layers_from_getcapabilities(mocker):
    from mapserver_tools.edit_wms_mmd_xml_files import edit_wms_mmd_xml_files
    mocker.patch('requests.get', side_effect=mocked_requests_get)
    ewmxf = edit_wms_mmd_xml_files()
    layers = ['hr_overview', 'ir_window_channel']
    assert ewmxf.read_layers_from_getcapabilities('https://some-host/?request=getcapabilities') == layers
