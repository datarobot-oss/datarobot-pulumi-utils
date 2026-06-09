# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from unittest.mock import MagicMock, patch

import pytest

from datarobot_pulumi_utils.common.urls import get_datarobot_url, get_deployment_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_client(external_url: str) -> MagicMock:
    """Return a mock DR client whose GET /clientConfig/ yields ``external_url``."""
    client = MagicMock()
    client.get.return_value.json.return_value = {"EXTERNAL_WEB_SERVER_URL": external_url}
    return client


# ---------------------------------------------------------------------------
# get_datarobot_url
# ---------------------------------------------------------------------------


class TestGetDatarobotUrlTier1ExplicitOverride:
    def test_returns_override_url_with_api_v2(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com")
        assert get_datarobot_url() == "https://override.example.com/api/v2"

    def test_strips_trailing_slash_and_appends_api_v2(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com/")
        assert get_datarobot_url() == "https://override.example.com/api/v2"

    def test_does_not_double_append_api_v2(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com/api/v2")
        assert get_datarobot_url() == "https://override.example.com/api/v2"

    def test_override_skips_api_call(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com")
        with patch("datarobot_pulumi_utils.common.urls.dr.client.get_client") as mock_get_client:
            get_datarobot_url()
            mock_get_client.assert_not_called()


class TestGetDatarobotUrlTier2ClientConfig:
    def test_returns_external_url_from_client_config_with_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "http://datarobot-nginx/api/v2")
        with patch(
            "datarobot_pulumi_utils.common.urls.dr.client.get_client",
            return_value=_mock_client("https://external.example.com"),
        ):
            assert get_datarobot_url() == "https://external.example.com/api/v2"

    def test_strips_trailing_slash_and_appends_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "http://datarobot-nginx/api/v2")
        with patch(
            "datarobot_pulumi_utils.common.urls.dr.client.get_client",
            return_value=_mock_client("https://external.example.com/"),
        ):
            assert get_datarobot_url() == "https://external.example.com/api/v2"

    def test_does_not_double_append_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "http://datarobot-nginx/api/v2")
        with patch(
            "datarobot_pulumi_utils.common.urls.dr.client.get_client",
            return_value=_mock_client("https://external.example.com/api/v2"),
        ):
            assert get_datarobot_url() == "https://external.example.com/api/v2"

    def test_falls_through_when_client_not_configured(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        with patch(
            "datarobot_pulumi_utils.common.urls.dr.client.get_client",
            side_effect=Exception("client not initialised"),
        ):
            result = get_datarobot_url()
        assert result == "https://app.datarobot.com/api/v2"

    def test_falls_through_on_network_error(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        client = MagicMock()
        client.get.side_effect = OSError("connection refused")
        with patch(
            "datarobot_pulumi_utils.common.urls.dr.client.get_client",
            return_value=client,
        ):
            result = get_datarobot_url()
        assert result == "https://app.datarobot.com/api/v2"


class TestGetDatarobotUrlTier3Fallback:
    def test_keeps_api_v2_suffix(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        assert get_datarobot_url() == "https://app.datarobot.com/api/v2"

    def test_strips_trailing_slash_preserves_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2/")
        assert get_datarobot_url() == "https://app.datarobot.com/api/v2"

    def test_airgapped_internal_url_returns_endpoint_with_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "http://datarobot-nginx/api/v2")
        assert get_datarobot_url() == "http://datarobot-nginx/api/v2"

    def test_default_endpoint_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.delenv("DATAROBOT_ENDPOINT", raising=False)
        assert get_datarobot_url() == "https://app.datarobot.com/api/v2"


# ---------------------------------------------------------------------------
# get_deployment_url
# ---------------------------------------------------------------------------


class TestGetDeploymentUrl:
    def test_uses_external_url_without_api_v2(self, monkeypatch):
        """get_deployment_url produces a web console URL, so /api/v2 must be stripped."""
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://dr.example.com")
        result = get_deployment_url("abc123")
        assert result == "https://dr.example.com/console-nextgen/deployments/abc123/"

    def test_fallback_base_url_without_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        result = get_deployment_url("dep456")
        assert result == "https://app.datarobot.com/console-nextgen/deployments/dep456/"
