import configparser
import json
import os
import tempfile
from distutils.dir_util import copy_tree
from pathlib import Path
from utils import generate_terraform_project


config_path = os.path.expanduser("~/tmp/olaclick/dgctl.json")
terraform_project_path = os.path.expanduser("~/tmp/olaclick/generated")

with open(config_path, 'r') as f:
    bundle_spec = json.loads(f.read())

home_path = str(Path.home())
with tempfile.TemporaryDirectory() as tmp_dir_name:
    generate_terraform_project(tmp_dir_name, "tf_templates/", bundle_spec)
    copy_tree(f"{tmp_dir_name}/terraform", terraform_project_path)

