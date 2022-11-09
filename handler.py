import json
import tempfile

from utils import generate_terraform_project


def generate_terraform(event, context):
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }
    use_temp_dir = True

    if use_temp_dir:
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            result = generate_terraform_project(tmp_dir_name)
            return result

    return {"statusCode": 200, "body": json.dumps(body)}