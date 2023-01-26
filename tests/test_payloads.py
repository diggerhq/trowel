import json
import pytest
from pydantic import ValidationError

from payloads import PayloadGenerateTerraform


class TestPayloadGenerateTerraforms:
    def test_empty_payload(self):
        with pytest.raises(ValidationError):
            PayloadGenerateTerraform.parse_obj({})

    def test_success(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "for_local_run": True,
                "id": "test-env-id",
                "blocks": [],
                "addons": [],
            }
        )

    @pytest.mark.parametrize(
        "missing_field", ["target", "aws_region", "id", "blocks"],
    )
    def test_missing_root_level_field(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "aws_region": "us-east-1",
            "id": "test-env-id",
            "blocks": [],
        }

        del payload[missing_field]

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": [missing_field],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]

    def test_block_vpc(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "aws_region": "us-east-1",
                "id": "test-env-id",
                "blocks": [
                    {
                        "name": "network-env-test-1",
                        "target": "diggerhq/target-network-module@main",
                        "type": "vpc",
                    },
                ],
            }
        )

    def test_block_container(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "aws_region": "us-east-1",
                "id": "test-env-id",
                "blocks": [
                    {
                        "name": "core-service-app",
                        "target": "diggerhq/target-ecs-module@dev",
                        "type": "container",
                        "aws_app_identifier": "core-service",
                    },
                ],
            }
        )

    def test_block_resource(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "aws_region": "us-east-1",
                "id": "test-env-id",
                "blocks": [
                    {
                        "name": "hubii-db",
                        "target": "diggerhq/target-resource-module@main",
                        "type": "resource",
                        "aws_app_identifier": "hubii-db",
                        "resource_type": "database",
                    },
                ],
            }
        )


    def test_missing_mandatory_field_in_vpc(self):
        # mandatory block name is missing
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "aws_region": "us-east-1",
            "id": "test-env-id",
            "blocks": [
                {
                    "target": "diggerhq/target-network-module@main",
                    "type": "vpc",
                },
            ],
        }

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["blocks", 0, "__root__"],
                "msg": f"Missing block name",
                "type": "value_error",
            }
        ]

    @pytest.mark.parametrize("missing_field", ("aws_app_identifier",))
    def test_missing_mandatory_field_in_container(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "aws_region": "us-east-1",
            "id": "test-env-id",
            "blocks": [
                {
                    "name": "core-service-app",
                    "target": "diggerhq/target-ecs-module@dev",
                    "type": "container",
                    "aws_app_identifier": "core-service",
                },
            ],
        }

        del payload["blocks"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["blocks", 0, "__root__"],
                "msg": f"Missing mandatory '{missing_field}' parameter in 'core-service-app' block",
                "type": "value_error",
            }
        ]

    @pytest.mark.parametrize("missing_field", ("resource_type", "aws_app_identifier",))
    def test_missing_mandatory_field_in_resource(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "aws_region": "us-east-1",
            "id": "test-env-id",
            "blocks": [
                {
                    "name": "hubii-db",
                    "target": "diggerhq/target-resource-module@main",
                    "type": "resource",
                    "aws_app_identifier": "hubii-db",
                    "resource_type": "database",
                },
            ],
        }

        del payload["blocks"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["blocks", 0, "__root__"],
                "msg": f"Missing mandatory '{missing_field}' parameter in 'hubii-db' block",
                "type": "value_error",
            }
        ]

    @pytest.mark.parametrize("block_name", ("999-starts-with-digit", ""))
    def test_block_name_negatively(self, block_name):
        with pytest.raises(ValidationError):
            assert PayloadGenerateTerraform.parse_obj(
                {
                    "target": "diggerhq/tf-module-bundler@master",
                    "aws_region": "us-east-1",
                    "id": "test-env-id",
                    "blocks": [
                        {
                            "name": block_name,
                            "target": "diggerhq/target-network-module@main",
                            "type": "vpc",
                        },
                    ],
                }
            )



    def test_load_balancer_disabled(self):
        with pytest.raises(ValidationError):
            assert PayloadGenerateTerraform.parse_obj(
                {
                    "target": "diggerhq/tf-module-bundler@master",
                    "aws_region": "us-east-1",
                    "id": "test-env-id",
                    "blocks": [
                        {
                            "name": "myapp",
                            "target": "diggerhq/target-network-module@main",
                            "type": "vpc",
                            "load_balancer": False,
                            "container_port": "8000"
                        },
                    ],
                }
            )

    def test_redis_mandatory_parameters(self):
        PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "aws_region": "us-east-1",
                "id": "test-env-id",
                "blocks": [
                    {
                        "name": "myapp",
                        "target": "diggerhq/target-network-module@main",
                        "type": "resource",
                        "aws_app_identifier": "redis",
                        "resource_type": "redis",
                        "redis_engine_version": "14"
                    },
                ],
            }
        )


    @pytest.mark.parametrize("missing_field", ("redis_engine_version",))
    def test_missing_mandatory_field_in_redis_resource(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "aws_region": "us-east-1",
            "id": "test-env-id",
            "blocks": [
                {
                    "name": "my-redis",
                    "target": "diggerhq/target-resource-module@main",
                    "type": "resource",
                    "aws_app_identifier": "my-redis",
                    "resource_type": "redis",
                },
            ],
        }

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["blocks", 0, "__root__"],
                "msg": f"Missing mandatory '{missing_field}' parameter in 'my-redis' block",
                "type": "value_error",
            }
        ]
