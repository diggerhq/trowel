def convert_string_to_hcl(t):
    return str(t).replace("'", '"')


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
