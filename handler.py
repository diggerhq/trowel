import json
import logging
import tempfile

from utils import generate_terraform_project


def generate_terraform(event, context):
    print(f'event: {event}, context: {context}')
    use_temp_dir = True

    if use_temp_dir:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            result = generate_terraform_project(tmp_dir_name, event)
            return result

    return {"statusCode": 200, "body": json.dumps({})}
