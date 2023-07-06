
def validate_bastion_parameters(config: dict):
    if "enable_bastion" in config:
        if not isinstance(config["enable_bastion"], bool):
            raise ValueError("enable_bastion is not boolean")
    if "bastion_ssh_key_name" not in config:
        raise ValueError("bastion_ssh_key_name is mandatory parameter if bastion is enabled")
    if "bastion_instance_name" not in config:
        raise ValueError("bastion_instance_name is mandatory parameter if bastion is enabled")
    if "bastion_allowed_hosts" not in config:
        raise ValueError("bastion_allowed_hosts is mandatory parameter if bastion is enabled")