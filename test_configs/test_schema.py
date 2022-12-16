import json
import pytest
from pydantic import ValidationError

from schema import LambdaPayload


class TestLambdaPayloads:
    def test_empty_payload(self):
        with pytest.raises(ValidationError):
            LambdaPayload.parse_obj({})

    def test_success(self):
        self.assertTrue(
            LambdaPayload.parse_obj(
                {
                    "target": "diggerhq/tf-module-bundler@master",
                    "for_local_run": True,
                    "aws_region": "us-east-1",
                    "environment_id": "test-env-id",
                    "modules": [],
                }
            )
        )

    @pytest.mark.parametrize(
        "missing_field",
        ["target", "for_local_run", "aws_region", "environment_id", "modules"],
    )
    def test_missing_root_level_field(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "for_local_run": True,
            "aws_region": "us-east-1",
            "environment_id": "test-env-id",
            "modules": [],
        }

        del payload[missing_field]

        with pytest.raises(ValidationError) as exinfo:
            LambdaPayload.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": [missing_field],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ]

    def test_module_vpc(self):
        self.assertTrue(
            LambdaPayload.parse_obj(
                {
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
                    ],
                }
            )
        )

    def test_module_container(self):
        self.assertTrue(
            LambdaPayload.parse_obj(
                {
                    "target": "diggerhq/tf-module-bundler@master",
                    "for_local_run": True,
                    "aws_region": "us-east-1",
                    "environment_id": "test-env-id",
                    "modules": [
                        {
                            "module_name": "core-service-app",
                            "target": "diggerhq/target-ecs-module@dev",
                            "type": "container",
                            "aws_app_identifier": "core-service",
                        },
                    ],
                }
            )
        )

    def test_module_resource(self):
        self.assertTrue(
            LambdaPayload.parse_obj(
                {
                    "target": "diggerhq/tf-module-bundler@master",
                    "for_local_run": True,
                    "aws_region": "us-east-1",
                    "environment_id": "test-env-id",
                    "modules": [
                        {
                            "module_name": "hubii-db",
                            "target": "diggerhq/target-resource-module@main",
                            "type": "resource",
                            "aws_app_identifier": "hubii-db",
                            "resource_type": "database",
                        },
                    ],
                }
            )
        )

    @pytest.mark.parametrize("missing_field", ("network_name",))
    def test_missing_mandatory_field_in_vpc(self, missing_field):
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
            ],
        }

        del payload["modules"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            LambdaPayload.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["modules", 0, "__root__"],
                "msg": f"Missing mandatory {missing_field} in network-env-test-1 module",
                "type": "value_error",
            }
        ]


    @pytest.mark.parametrize("missing_field", ("aws_app_identifier",))
    def test_missing_mandatory_field_in_container(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "for_local_run": True,
            "aws_region": "us-east-1",
            "environment_id": "test-env-id",
            "modules": [
                {
                    "module_name": "core-service-app",
                    "target": "diggerhq/target-ecs-module@dev",
                    "type": "container",
                    "aws_app_identifier": "core-service",
                },
            ],
        }

        del payload["modules"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            LambdaPayload.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["modules", 0, "__root__"],
                "msg": f"Missing mandatory {missing_field} in core-service-app module",
                "type": "value_error",
            }
        ]

    @pytest.mark.parametrize("missing_field", ("resource_type", "aws_app_identifier",))
    def test_missing_mandatory_field_in_resource(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "for_local_run": True,
            "aws_region": "us-east-1",
            "environment_id": "test-env-id",
            "modules": [
                {
                    "module_name": "hubii-db",
                    "target": "diggerhq/target-resource-module@main",
                    "type": "resource",
                    "aws_app_identifier": "hubii-db",
                    "resource_type": "database",
                },
            ],
        }

        del payload["modules"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            LambdaPayload.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["modules", 0, "__root__"],
                "msg": f"Missing mandatory {missing_field} in hubii-db module",
                "type": "value_error",
            }
        ]
