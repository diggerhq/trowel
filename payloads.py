import json
from enum import Enum
from typing import List, Optional, Dict

from pydantic import BaseModel, ValidationError, constr, root_validator, validator

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
    key: constr(min_length=1)
    value: str


class Block(BaseModel):
    name: constr(min_length=1)
    target: constr(min_length=1)

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
    secrets: Optional[Dict[str, str]]
    env_mapping: Optional[List[str]]
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
    custom_terraform: Optional[str]
    imported_id: Optional[str]

    @root_validator(pre=True)
    def block_has_mandatory_data(cls, values):

        if "type" not in values:
            return values

        if "name" not in values:
            raise ValueError(f"Missing block name")

        block_name = values["type"]
        name = values["name"]

        for required_field in cls.Config.required_by_block[block_name]:
            if values.get(required_field) is None:
                raise ValueError(f"Missing mandatory '{required_field}' parameter in '{name}' block")

        return values

    @validator("name")
    def name_cannot_start_with_number(cls, v):
        if v[0].isnumeric():
            raise ValueError("Block name cannot start with number")

        return v

    @root_validator(pre=True)
    def load_balancer_disabled(cls, values):
        if "load_balancer" in values and not values["load_balancer"]:
            if "container_port" in values:
                raise ValueError("If load_balance=False, container_port parameter can't be used.")
        return values

    @root_validator(pre=True)
    def redis_mandatory_parameters(cls, values):
        print(f'redis_mandatory_parameters: {values}')
        if (
            "type" in values
            and values["type"] == "resource"
            and "resource_type" in values
            and values["resource_type"] == "redis"
        ):
            if "redis_engine_version" not in values:
                raise ValueError(f"Missing mandatory 'redis_engine_version' parameter in '{values['name']}' block")
        return values

    class Config:
        # Declare which fields are mandatory for given block type
        required_by_block = {
            BlockTypeEnum.vpc.value: (),
            BlockTypeEnum.container.value: ("aws_app_identifier",),
            BlockTypeEnum.resource.value: (
                "resource_type",
                "aws_app_identifier",
            ),
        }


class PayloadGenerateTerraform(BaseModel):
    target: constr(min_length=1)
    for_local_run: Optional[bool]
    aws_region: constr(min_length=1)
    id: constr(min_length=1)
    datadog_enabled: Optional[bool]

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
