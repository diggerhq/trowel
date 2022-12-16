import base64
import configparser
import json

import boto3

client = boto3.client("sts")
print(client.get_caller_identity())

ssm = boto3.client("ssm")


with open("./test_configs/digger.json", "r") as f:
    bundle_spec = json.loads(f.read())

bundle_name = bundle_spec["environment_id"]
config = configparser.ConfigParser()
# without this line all keys will be in lower case
config.optionxform = str
config.read("./test_configs/digger.ini")

for k, v in config["secrets"].items():
    val = v
    if v.startswith("arn:aws:ssm"):
        name = v[v.index(':parameter') + len(':parameter'):]
        print(name)
        result = ssm.get_parameter(Name=name, WithDecryption=True)
        if "Parameter" in result and "Value" in result["Parameter"]:
            response = ssm.put_parameter(
            Name=f"/{bundle_name}/{k.lower()}", Value=result["Parameter"]["Value"], Type="SecureString", Overwrite=True
            )
    else:
        response = ssm.put_parameter(
            Name=f"/{bundle_name}/{k.lower()}", Value=v, Type="SecureString", Overwrite=True
        )