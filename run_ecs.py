import configparser
import json
import os
from distutils.dir_util import copy_tree
from pathlib import Path
from utils import generate_terraform_project

config = configparser.ConfigParser()
# without this line all keys will be in lower case
config.optionxform = str

current_dir = os.getcwd()

with open('./test_configs/hubii_minimal.json', 'r') as f:
    bundle_spec = json.loads(f.read())
config.read('./test_configs/hubii.ini')

if not 'secrets' in bundle_spec:
    bundle_spec['secrets'] = []
#for k, v in config['secrets'].items():
#    bundle_spec['secrets'].append(str(k))

for m in bundle_spec['blocks']:
    if m['type'] == 'container':
        pass
#        for k, v in config['envs'].items():
#            m['environment_variables'].append({'key': k, 'value': v})
        #for k, v in config['secrets'].items():
        #    m['secrets'].append(str(k))

home_path = str(Path.home())
generate_terraform_project(f"{home_path}/tmp/hubii", bundle_spec)
copy_tree(f"{home_path}/tmp/hubii/terraform", f"{home_path}/tmp/test-hubii")

