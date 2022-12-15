from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, root_validator


class ModuleTypeEnum(Enum):
    vpc = "vpc"
    container = "container"
    resource = "resource"


class ResourceTypeEnum(Enum):
    database = "database"
    redis = "redis"


class Module(BaseModel):
    module_name: str
    target: str
    type: ModuleTypeEnum

    # vpc
    network_name: Optional[str]
    enable_vpc_endpoints: Optional[bool]
    enable_dns_hostnames: Optional[bool]
    enable_dns_support: Optional[bool]
    one_nat_gateway_per_az: Optional[bool]
    enable_nat_gateway: Optional[bool]

    # container
    aws_app_identifier: Optional[str]

    # resource
    resource_type: Optional[ResourceTypeEnum]

    @root_validator
    def module_has_mandatory_data(cls, values):
        if "type" not in values:
            return values

        module_type = values["type"]
        module_name = values["module_name"]

        for required_field in cls.Config.required_by_module[module_type]:
            if required_field not in values:
                raise ValueError(
                    f"{required_field} is mandatory for {module_type} module. Check {module_name}"
                )

        return values

    class Config:
        # Declare which fields are mandatory for given module type
        required_by_module = {
            ModuleTypeEnum.vpc: ("network_name",),
            ModuleTypeEnum.container: ("aws_app_identifier",),
            ModuleTypeEnum.resource: ("resource_type", "aws_app_identifier",),
        }


class MySchema(BaseModel):
    target: str
    for_local_run: bool
    aws_region: str
    environment_id: str
    secret_keys: Optional[List] = []
    hosted_zone_name: Optional[str]
    modules: List[Module]


if __name__ == "__main__":
    MySchema.parse_file("digger.json")
    MySchema.parse_file("hubii.json")

    payload = {
        "target": "diggerhq/tf-module-bundler@master",
        "for_local_run": True,
        "aws_region": "us-east-1",
        "environment_id": "test-env-id",
        "modules": [
            {
                "module_name": "network-env-test-1",
                "target": "diggerhq/target-network-module@main",
                "type": "vpc",
                "network_name": "env-test-1",
            },
            {
                "module_name": "core-service-app",
                "target": "diggerhq/target-ecs-module@dev",
                "type": "container",
                "aws_app_identifier": "core-service",
            },
            {
                "module_name": "hubii-db",
                "target": "diggerhq/target-resource-module@main",
                "type": "resource",
                "aws_app_identifier": "hubii-db",
                "resource_type": "database",
            },
        ],
    }

    MySchema.parse_obj(payload)
