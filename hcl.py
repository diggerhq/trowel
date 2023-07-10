def convert_string_to_hcl(t):
    return str(t).replace("'", '"')


def convert_secrets_list_to_hcl(secrets, secret_mappings, aws_region, aws_account_id) -> str:
    result = "[\n"
    for s in secrets:
        result += '{ "key": "' + s['key'] + f'", "value": "arn:aws:ssm:{aws_region}:{aws_account_id}:parameter' + s['value'] + '"},\n'
    for s in secret_mappings:
        result += '{ "key": "' + s['key'] + '", "value": ' + s['value'] + '},\n'
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
        config["bastion_allowed_hosts"] = convert_string_to_hcl(config["bastion_allowed_hosts"])
    return config
