from distutils.util import strtobool

def validate_bastion_parameters(config: dict):
    if "enable_bastion" in config:
        enable_bastion = strtobool(config["enable_bastion"])
    if "bastion_ssh_key_name" not in config:
        raise ValueError("bastion_ssh_key_name is mandatory parameter if bastion is enabled")
    if "bastion_instance_name" not in config:
        raise ValueError("bastion_instance_name is mandatory parameter if bastion is enabled")
    if "bastion_allowed_hosts" not in config:
        raise ValueError("bastion_allowed_hosts is mandatory parameter if bastion is enabled")