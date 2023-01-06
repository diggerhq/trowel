import json
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ValidationError, root_validator

from exceptions import PayloadValidationException


class BlockTypeEnum(Enum):
    vpc = "vpc"
    container = "container"
    resource = "resource"
    imported = "imported"


class ResourceTypeEnum(Enum):
    database = "database"
    redis = "redis"


class LaunchTypeEnum(Enum):
    fargate = "FARGATE"


class RdsEngineEnum(Enum):
    postgres = "postgres"


class EnvironmentVariable(BaseModel):
    key: str
    value: str


class Block(BaseModel):
    name: str
    target: Optional[str]
    type: BlockTypeEnum

    # vpc
    enable_vpc_endpoints: Optional[bool]
    enable_dns_hostnames: Optional[bool]
    enable_dns_support: Optional[bool]
    one_nat_gateway_per_az: Optional[bool]
    enable_nat_gateway: Optional[bool]

    # container
    aws_app_identifier: Optional[str]
    provider: Optional[str]
    region: Optional[str]
    task_memory: Optional[int]
    task_cpu: Optional[int]
    container_port: Optional[int]
    load_balancer: Optional[bool]
    internal: Optional[bool]
    health_check: Optional[str]
    health_check_matcher: Optional[str]
    monitoring_enabled: Optional[bool]
    lb_monitoring_enabled: Optional[bool]
    launch_type: Optional[LaunchTypeEnum]
    environment_variables: Optional[List[EnvironmentVariable]]
    secret_keys: Optional[List[str]]
    secrets_mapping: Optional[List[str]]
    env_mapping: Optional[List[str]]
    secrets: Optional[List[str]]
    task_cpu: Optional[int]
    task_mem: Optional[int]

    # resource
    resource_type: Optional[ResourceTypeEnum]
    id: Optional[str]
    rds_engine: Optional[RdsEngineEnum]
    rds_engine_version: Optional[str]
    database_name: Optional[str]
    database_username: Optional[str]
    rds_instance_class: Optional[str]
    connection_schema: Optional[str]
    date_created: Optional[str]

    # imported
    custom_terraform: Optional[List[Dict[str, str]]]
    imported_id: Optional[str]

    @root_validator
    def module_has_mandatory_data(cls, values):
        if "type" not in values:
            return values

        module_type = values["type"]
        name = values["name"]

        for required_field in cls.Config.required_by_module[module_type]:
            if values[required_field] is None:
                raise ValueError(f"Missing mandatory {required_field} in {name} module")

        return values

    class Config:
        # Declare which fields are mandatory for given module type
        required_by_module = {
            BlockTypeEnum.vpc: (),
            BlockTypeEnum.container: ("aws_app_identifier",),
            BlockTypeEnum.resource: ("resource_type", "aws_app_identifier",),
            BlockTypeEnum.imported: ("custom_terraform",),
        }


class PayloadGenerateTerraform(BaseModel):
    target: str
    for_local_run: Optional[bool]
    aws_region: str
    id: str
    blocks: List[Block]

    secret_keys: Optional[List] = []
    hosted_zone_name: Optional[str]
    created: Optional[int]


def validate_payload(payload, cls):
    try:
        cls.parse_obj(payload)
    except ValidationError as err:
        raise PayloadValidationException(json.dumps(json.loads(err.json())))
    except ValueError as err:
        raise PayloadValidationException(str(err))


if __name__ == "__main__":
    PayloadGenerateTerraform.parse_file("digger.json")
    PayloadGenerateTerraform.parse_file("hubii.json")
    PayloadGenerateTerraform.parse_file("test.json")

    payload = {
        "target": "diggerhq/tf-module-bundler@master",
        "for_local_run": True,
        "aws_region": "us-east-1",
        "id": "test-env-id",
        "blocks": [
            {
                "name": "network-env-test-1",
                "target": "diggerhq/target-network-module@main",
                "type": "vpc",
            },
            {
                "name": "core-service-app",
                "target": "diggerhq/target-ecs-module@dev",
                "type": "container",
                "aws_app_identifier": "core-service",
            },
            {
                "name": "hubii-db",
                "target": "diggerhq/target-resource-module@main",
                "type": "resource",
                "aws_app_identifier": "hubii-db",
                "resource_type": "database",
            },
        ],
    }

    try:
        PayloadGenerateTerraform.parse_obj(payload)
    except ValidationError as err:
        error_str = err.json()
        print(type(error_str), error_str)
