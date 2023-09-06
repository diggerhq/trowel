import re


def convert_string_to_hcl(t):
    return str(t).replace("'", '"')


def replace_terraform_parameters(s: str):
    """
    replaces strings like "##module.oc-services-redis-qa.redis_url##" with module.oc-services-redis-qa.redis_url
    :param s:
    :return:
    """
    matches = re.finditer(r'\"##(.*)##\"', s, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        print(f"++++++++++++++++   {match.group(0)}, {match.group(1)}")
        s = s.replace(match.group(0), match.group(1))
    return s

def convert_secrets_list_to_hcl(
    secrets: list, secret_mappings: list, aws_region: str, aws_account_id: str
) -> str:
    """
    secret_mappings item are converted to terraform references without quotes
    secrets items should start with a '/' (ex: /dev/database_password) and arn prefix is being added
    :param secrets:
    :param secret_mappings:
    :param aws_region:
    :param aws_account_id:
    :return:
    """
    result = "[\n"
    for s in secrets:
        secret_arn = f"arn:aws:ssm:${{var.aws_region}}:${{var.aws_account_id}}:parameter{s['value']}"
        result += '{ "key": "' + s["key"] + '", "value": "' + secret_arn + '" },\n'
    for s in secret_mappings:
        result += '{ "key": "' + s["key"] + '", "value": ' + s["value"] + "},\n"
    result += "]\n"
    return result


def convert_dict_to_hcl(d: dict):
    result = "{"
    for k, v in d.items():
        result += f'"{k}"="{v}",'
    result += "}"
    return result


def convert_config_parameters_to_hcl(config: dict):
    if "bastion_allowed_hosts" in config:
        config["bastion_allowed_hosts"] = convert_string_to_hcl(
            config["bastion_allowed_hosts"]
        )
    return config
