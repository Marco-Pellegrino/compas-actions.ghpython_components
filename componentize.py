from __future__ import print_function

import argparse
import base64
import json
import os
import re
import sys

import clr
import System
import System.IO

GHPYTHON_SCRIPT_GUID = System.Guid('410755b1-224a-4c1e-a407-bf32fb45ea7e')
TEMPLATE_VER = re.compile('{{version}}')
TEMPLATE_NAME = re.compile('{{name}}')
TEMPLATE_GHUSER_NAME = re.compile('{{ghuser_name}}')

TYPES_MAP = dict(
    none='35915213-5534-4277-81b8-1bdc9e7383d2',
    ghdoc='87f87f55-5b71-41f4-8aea-21d494016f81',
    float='39fbc626-7a01-46ab-a18e-ec1c0c41685b',
    bool='d60527f5-b5af-4ef6-8970-5f96fe412559',
    int='48d01794-d3d8-4aef-990e-127168822244',
    complex='309690df-6229-4774-91bb-b1c9c0bfa54d',
    str='37261734-eec7-4f50-b6a8-b8d1f3c4396b',
    datetime='09bcf900-fe83-4efa-8d32-33d89f7a3e66',
    guid='5325b8e1-51d7-4d36-837a-d98394626c35',
    color='24b1d1a3-ab79-498c-9e44-c5b14607c4d3',
    point='e1937b56-b1da-4c12-8bd8-e34ee81746ef',
    vector='15a50725-e3d3-4075-9f7c-142ba5f40747',
    plane='3897522d-58e9-4d60-b38c-978ddacfedd8',
    interval='589748aa-e558-4dd9-976f-78e3ab91fc77',
    uvinterval='74c906f3-db02-4cea-bd58-de375cb5ae73',
    box='f29cb021-de79-4e63-9f04-fc8e0df5f8b6',
    transform='c4b38e4c-21ff-415f-a0d1-406d282428dd',
    line='f802a8cd-e699-4a94-97ea-83b5406271de',
    circle='3c5409a1-3293-4181-a6fa-c24c37fc0c32',
    arc='9c80ec18-b48c-41b0-bc6e-cd93d9c916aa',
    polyline='66fa617b-e3e8-4480-9f1e-2c0688c1d21b',
    rectangle='83da014b-a550-4bf5-89ff-16e54225bd5d',
    curve='9ba89ec2-5315-435f-a621-b66c5fa2f301',
    mesh='794a1f9d-21d5-4379-b987-9e8bbf433912',
    surface='f4070a37-c822-410f-9057-100d2e22a22d',
    subd='20f4ca9c-6c90-4fd6-ba8a-5bf9ca79db08',
    brep='2ceb0405-fdfe-403d-a4d6-8786da45fb9d',
)

EXPOSURE = dict(
    valid=set([-1, 2, 4, 8, 16, 32, 64, 128]),
    default=2
)
ACCESS = dict(
    valid=set([0, 1, 2]),
    map=dict(item=0, list=1, tree=2),
    default=0
)
PARAM_TYPE = dict(
    valid=set(TYPES_MAP.values()),
    map=TYPES_MAP,
    default=TYPES_MAP['ghdoc']
)
WIRE_DISPLAY = dict(
    valid=set([0, 1, 2]),
    map=dict(default=0, faint=1, hidden=2),
    default=0
)


def find_ghio_assembly(libdir):
    for root, _dirs, files in os.walk(libdir):
        for basename in files:
            if basename.upper() == 'GH_IO.DLL':
                filename = os.path.join(root, basename)
                return filename


def bitmap_from_image_path(image_path):
    with open(image_path, "rb") as imageFile:
        img_string = base64.b64encode(imageFile.read())
    return System.Convert.FromBase64String(img_string)


def validate_source_bundle(source):
    icon = os.path.join(source, 'icon.png')
    code = os.path.join(source, 'code.py')
    data = os.path.join(source, 'metadata.json')

    if not os.path.exists(icon):
        raise ValueError('icon missing, make sure icon.png is present in the source bundle: {}'.format(source))
    if not os.path.exists(code):
        raise ValueError('code missing, make sure code.py is present in the source bundle: {}'.format(source))
    if not os.path.exists(data):
        raise ValueError('metadata missing, make sure metadata.json is present in the source bundle: {}'.format(source))

    icon = bitmap_from_image_path(icon)
    
    with open(code, 'r') as f:
        code = f.read()

    with open(data, 'r') as f:
        data = json.load(f)

    if 'exposure' not in data:
        data['exposure'] = EXPOSURE['default']
    
    if data['exposure'] not in EXPOSURE['valid']:
        raise ValueError('Invalid exposure value. Accepted values are {}'.format(sorted(EXPOSURE['valid'])))

    return icon, code, data


def parse_param_access(access):
    try:
        access = int(access)
    except ValueError:
        # Maybe string?
        access = ACCESS['map'].get(access)
    
    if access not in ACCESS['valid']:
        raise ValueError('Invalid param access value. Valid values are {}'.format(sorted(ACCESS['valid'])))

    return access


def parse_wire_display(wire_display):
    try:
        wire_display = int(wire_display)
    except ValueError:
        wire_display = WIRE_DISPLAY['map'].get(wire_display)

    if wire_display not in WIRE_DISPLAY['valid']:
        raise ValueError('Invalid wire display value. Valid values are {}'.format(
            sorted(WIRE_DISPLAY['valid'])))

    return wire_display


def parse_param_type_hint(type_hint_id):
    type_hint_id = type_hint_id or PARAM_TYPE['default']

    if type_hint_id in TYPES_MAP:
        type_hint_id = TYPES_MAP[type_hint_id]

    if type_hint_id not in PARAM_TYPE['valid']:
        raise ValueError('Invalid param type hint ID ("{}"). Valid values are {}'.format(type_hint_id, sorted(PARAM_TYPE['valid'])))

    try:
        type_hint_id = System.Guid.Parse(type_hint_id)
    except SystemError:
        raise ValueError('Unable to parse type hint ID: {}'.format(type_hint_id))

    return type_hint_id

def replace_templates(code, version, name, ghuser_name):
    if version:
        code = TEMPLATE_VER.sub(version, code)

    code = TEMPLATE_NAME.sub(name, code)
    code = TEMPLATE_GHUSER_NAME.sub(ghuser_name, code)

    return code


def create_ghuser_component(source, target, version=None):
    from GH_IO.Serialization import GH_LooseChunk
    icon, code, data = validate_source_bundle(source)

    code = replace_templates(
        code, version, data['name'], os.path.basename(target))

    instance_guid = data.get('instanceGuid')
    if not instance_guid:
        instance_guid = System.Guid.NewGuid()
    else:
        instance_guid = System.Guid.Parse(instance_guid)

    root = GH_LooseChunk('UserObject')

    root.SetGuid('BaseID', GHPYTHON_SCRIPT_GUID)
    root.SetString('Name', data['name'])
    root.SetString('NickName', data['nickname'])
    root.SetString('Description', data.get('description', ''))
    root.SetInt32('Exposure', data.get('exposure', EXPOSURE['default']))
    root.SetString('Category', data['category'])
    root.SetString('SubCategory', data['subcategory'])
    root.SetGuid('InstanceGuid', instance_guid)
    root.SetByteArray('Icon', icon)

    ghpython_data = data['ghpython']
    ghpython_root = GH_LooseChunk('UserObject')
    ghpython_root.SetString('Description', data.get('description', ''))
    ghpython_root.SetBoolean('HideOutput', ghpython_data.get('hideOutput', True))
    ghpython_root.SetBoolean('HideInput', ghpython_data.get('hideInput', True))
    ghpython_root.SetBoolean('IsAdvancedMode', ghpython_data.get('isAdvancedMode', False))
    ghpython_root.SetInt32('IconDisplay', ghpython_data.get('iconDisplay', 0))
    ghpython_root.SetString('Name', data['name'])
    ghpython_root.SetString('NickName', data['nickname'])
    ghpython_root.SetBoolean('MarshalOutGuids', ghpython_data.get('marshalOutGuids', True))
    ghpython_root.SetString('CodeInput', code)
    
    # ghpython_root.CreateChunk('Attributes')
    # for mf in ('Bounds', 'Pivot', 'Selected'):
    params = ghpython_root.CreateChunk('ParameterData')
    inputParam = ghpython_data.get('inputParameters', [])
    outputParam = ghpython_data.get('outputParameters', [])

    params.SetInt32('InputCount', len(inputParam))
    for i, _pi in enumerate(inputParam):
        params.SetGuid('InputId', i,
                       System.Guid.Parse('84fa917c-1ed8-4db3-8be1-7bdc4a6495a2'))
    params.SetInt32('OutputCount', len(outputParam))
    for i, _po in enumerate(outputParam):
        params.SetGuid('OutputId', i,
                       System.Guid.Parse('8ec86459-bf01-4409-baee-174d0d2b13d0'))

    for i, pi in enumerate(inputParam):
        input_instance_guid = System.Guid.NewGuid()
        pi_chunk = params.CreateChunk('InputParam', i)
        pi_chunk.SetString('Name', pi['name'])
        pi_chunk.SetString('NickName', pi.get('nickname') or pi['name'])
        pi_chunk.SetString('Description', pi.get('description'))
        pi_chunk.SetBoolean('Optional', pi.get('optional', True))
        pi_chunk.SetBoolean('AllowTreeAccess', pi.get('allowTreeAccess', True))
        pi_chunk.SetBoolean('ShowTypeHints', pi.get('showTypeHints', True))
        pi_chunk.SetInt32('ScriptParamAccess', parse_param_access(pi.get('scriptParamAccess', ACCESS['default'])))
        pi_chunk.SetInt32('SourceCount', 0)
        pi_chunk.SetGuid('InstanceGuid', input_instance_guid)
        pi_chunk.SetGuid('TypeHintID', parse_param_type_hint(pi.get('typeHintID')))
        pi_chunk.SetInt32('WireDisplay', parse_wire_display(pi.get('wireDisplay', WIRE_DISPLAY['default'])))

    for i, po in enumerate(outputParam):
        output_instance_guid = System.Guid.NewGuid()
        po_chunk = params.CreateChunk('OutputParam', i)
        po_chunk.SetString('Name', po['name'])
        po_chunk.SetString('NickName', po.get('nickname') or po['name'])
        po_chunk.SetString('Description', po.get('description'))
        po_chunk.SetBoolean('Optional', po.get('optional', False))
        po_chunk.SetInt32('SourceCount', 0)
        po_chunk.SetGuid('InstanceGuid', output_instance_guid)

    # print(ghpython_root.Serialize_Xml())
    root.SetByteArray('Object', ghpython_root.Serialize_Binary())

    System.IO.File.WriteAllBytes(target, root.Serialize_Binary())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create GHUser components out of python code.')
    parser.add_argument('source', type=str, help='Source directory where code for all components is stored')
    parser.add_argument('target', type=str, help='Target directory for ghuser files')
    parser.add_argument('--ghio', type=str, required=False, help='Folder where the GH_IO.dll assembly is located. Defaults to ./lib')
    parser.add_argument('--version', type=str, required=False, help='Version to tag components')
    args = parser.parse_args()

    sourcedir = args.source
    if not os.path.isabs(sourcedir):
        sourcedir = os.path.abspath(sourcedir)

    targetdir = args.target
    if not os.path.isabs(targetdir):
        targetdir = os.path.abspath(targetdir)

    if args.ghio is None:
        here = os.path.dirname(os.path.abspath(__file__))
        libdir = os.path.join(here, 'lib')
    else:
        libdir = os.path.abspath(args.ghio)
    gh_io = find_ghio_assembly(libdir)
    print(libdir)
    print('################')
    source_bundles = [d for d in os.listdir(sourcedir)
                      if os.path.isdir(os.path.join(sourcedir, d)) and d not in ('__pycache__', '.git')]

    print('GHPython componentizer')
    print('======================')

    print('[x] Source: {} ({} components)'.format(sourcedir, len(source_bundles)))
    print('[ ] Target: {}\r'.format(targetdir), end='')
    if not os.path.exists(targetdir):
        os.mkdir(targetdir)
    print('[x]')

    print('[ ] GH_IO assembly: {}\r'.format(gh_io or args.ghio), end='')
    if not gh_io:
        print('[-]')
        print('    Cannot find GH_IO Assembly! Aborting.')
        sys.exit(-1)
    clr.AddReferenceToFileAndPath(gh_io)
    print('[x]')
    print()

    print('Processing component bundles:')
    for d in source_bundles:
        source = os.path.join(sourcedir, d)
        target = os.path.join(targetdir, d + '.ghuser')
        print('  [ ] {}\r'.format(d), end='')
        create_ghuser_component(source, target, args.version)
        print('  [x] {} => {}'.format(d, target))

