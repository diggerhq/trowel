import json
import tempfile
import traceback

from exceptions import PayloadValidationException, LambdaError
from utils import generate_terraform_project


def generate_terraform(event, context):
    print(f'event: {event}, context: {context}')
    use_temp_dir = True

    try:
        if use_temp_dir:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                result = generate_terraform_project(tmp_dir_name, event)
                return result
    except LambdaError as le:
        print(f"generate_terraform: lambda error: {le}")
        return {"statusCode": 500, "error": le.message}
    except Exception as e:
        print(f"generate_terraform: exception: {traceback.format_exc()}")
        return {"statusCode": 500, "error": str(e)}
    return {"statusCode": 200, "body": json.dumps({})}
