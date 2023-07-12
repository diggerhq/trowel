import configparser
import json
import os
import tempfile
from distutils.dir_util import copy_tree
from pathlib import Path
from utils import generate_terraform_project


config_path = os.path.expanduser("~/tmp/olaclick/dgctl.json")
config_dir = os.path.expanduser("~/tmp/olaclick")
terraform_project_path = os.path.expanduser("~/tmp/olaclick/qa")

config_path = os.path.expanduser("~/projects/cloud-infra/dgctl.json")
config_dir = os.path.expanduser("~/projects/cloud-infra")
terraform_project_path = os.path.expanduser("~/projects/cloud-infra/generated")

with open(config_path, 'r') as f:
    bundle_spec = json.loads(f.read())

home_path = str(Path.home())
with tempfile.TemporaryDirectory() as tmp_dir_name:
    generate_terraform_project(tmp_dir_name, "tf_templates/", bundle_spec, config_dir)
    copy_tree(f"{tmp_dir_name}/terraform", terraform_project_path)

