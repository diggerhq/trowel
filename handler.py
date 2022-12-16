import json
import tempfile
import traceback

from pydantic import ValidationError

from exceptions import PayloadValidationException, LambdaError
from payloads import PayloadGenerateTerraform
from utils import generate_terraform_project


def generate_terraform(event, context):
    print(f'event: {event}, context: {context}')
    use_temp_dir = True
       
    # check if event is coming from direct invocation or url invocation
    if "body" in event:
        payload = json.loads(event["body"])
    else:
        payload = event

    try:
        PayloadGenerateTerraform.parse_obj(payload)
    except ValidationError as err:
        print(f"generate_terraform: invalid payload: {err}")
        return {"statusCode": 500, "error": json.dumps(json.loads(err.json()))}
    except Exception as err:
        print(f"generate_terraform: failed to validate payload: {err}")
        return {"statusCode": 500, "error": str(err)}
        
    try:
        if use_temp_dir:
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                result = generate_terraform_project(tmp_dir_name, payload)
                return result
    except LambdaError as le:
        print(traceback.format_exc())
        print(f"generate_terraform: lambda error: {le}")
        return {"statusCode": 500, "error": le.message}
    except Exception as e:
        print(f"generate_terraform: exception: {traceback.format_exc()}")
        return {"statusCode": 500, "error": str(e)}
    return {"statusCode": 200, "body": json.dumps({})}
