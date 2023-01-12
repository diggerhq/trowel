import json
import pytest
from handler import generate_terraform


class TestLambdaPayloads:
    def test_generate_terraform_missing_blocks(self):
        response = generate_terraform({}, None)
        assert response["statusCode"] == 500
        assert "blocks" in response["error"]
