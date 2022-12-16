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
                "aws_region": "us-east-1",
                "environment_id": "test-env-id",
                "blocks": [],
            }
        )

    @pytest.mark.parametrize(
        "missing_field",
        ["target", "for_local_run", "aws_region", "environment_id", "blocks"],
    )
    def test_missing_root_level_field(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "for_local_run": True,
            "aws_region": "us-east-1",
            "environment_id": "test-env-id",
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

    def test_module_vpc(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "for_local_run": True,
                "aws_region": "us-east-1",
                "environment_id": "test-env-id",
                "blocks": [
                    {
                        "name": "network-env-test-1",
                        "target": "diggerhq/target-network-module@main",
                        "type": "vpc",
                    },
                ],
            }
        )

    def test_module_container(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "for_local_run": True,
                "aws_region": "us-east-1",
                "environment_id": "test-env-id",
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

    def test_module_resource(self):
        assert PayloadGenerateTerraform.parse_obj(
            {
                "target": "diggerhq/tf-module-bundler@master",
                "for_local_run": True,
                "aws_region": "us-east-1",
                "environment_id": "test-env-id",
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

    @pytest.mark.parametrize("missing_field", ())
    def test_missing_mandatory_field_in_vpc(self, missing_field):
        payload = {
            "target": "diggerhq/tf-module-bundler@master",
            "for_local_run": True,
            "aws_region": "us-east-1",
            "environment_id": "test-env-id",
            "blocks": [
                {
                    "name": "network-env-test-1",
                    "target": "diggerhq/target-network-module@main",
                    "type": "vpc",
                },
            ],
        }

        del payload["blocks"][0][missing_field]

        with pytest.raises(ValidationError) as exinfo:
            PayloadGenerateTerraform.parse_obj(payload)

        assert json.loads(exinfo.value.json()) == [
            {
                "loc": ["blocks", 0, "__root__"],
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
                "msg": f"Missing mandatory {missing_field} in hubii-db module",
                "type": "value_error",
            }
        ]
