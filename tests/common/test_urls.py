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
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from unittest.mock import patch

import pytest

from datarobot_pulumi_utils.common.urls import get_datarobot_url, get_deployment_url


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client_config_server(external_url: str) -> tuple[HTTPServer, int]:
    """Spin up a minimal HTTP server that returns a /clientConfig/ response."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = json.dumps({"EXTERNAL_WEB_SERVER_URL": external_url}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # suppress test output
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


# ---------------------------------------------------------------------------
# get_datarobot_url
# ---------------------------------------------------------------------------


class TestGetDatarobotUrlTier1ExplicitOverride:
    def test_returns_override_url(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com")
        assert get_datarobot_url() == "https://override.example.com"

    def test_strips_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com/")
        assert get_datarobot_url() == "https://override.example.com"

    def test_override_skips_api_call(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://override.example.com")
        monkeypatch.setenv("DATAROBOT_API_TOKEN", "tok")
        with patch("urllib.request.urlopen") as mock_open:
            get_datarobot_url()
            mock_open.assert_not_called()


class TestGetDatarobotUrlTier2ClientConfig:
    def test_returns_external_url_from_client_config(self, monkeypatch):
        server, port = _make_client_config_server("https://external.example.com")
        try:
            monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
            monkeypatch.setenv("DATAROBOT_ENDPOINT", f"http://127.0.0.1:{port}/api/v2")
            monkeypatch.setenv("DATAROBOT_API_TOKEN", "testtoken")
            result = get_datarobot_url()
            assert result == "https://external.example.com"
        finally:
            server.shutdown()

    def test_strips_trailing_slash_from_client_config(self, monkeypatch):
        server, port = _make_client_config_server("https://external.example.com/")
        try:
            monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
            monkeypatch.setenv("DATAROBOT_ENDPOINT", f"http://127.0.0.1:{port}/api/v2")
            monkeypatch.setenv("DATAROBOT_API_TOKEN", "testtoken")
            result = get_datarobot_url()
            assert result == "https://external.example.com"
        finally:
            server.shutdown()

    def test_skips_api_call_when_no_token(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        with patch("urllib.request.urlopen") as mock_open:
            get_datarobot_url()
            mock_open.assert_not_called()

    def test_falls_through_on_network_error(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        monkeypatch.setenv("DATAROBOT_API_TOKEN", "tok")
        with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
            result = get_datarobot_url()
        # Should fall through to tier 3
        assert result == "https://app.datarobot.com"


class TestGetDatarobotUrlTier3Fallback:
    def test_strips_api_v2_suffix(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        assert get_datarobot_url() == "https://app.datarobot.com"

    def test_strips_trailing_slash_before_api_v2(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2/")
        assert get_datarobot_url() == "https://app.datarobot.com"

    def test_airgapped_internal_url_returns_base(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "http://datarobot-nginx/api/v2")
        assert get_datarobot_url() == "http://datarobot-nginx"

    def test_default_endpoint_when_env_unset(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.delenv("DATAROBOT_ENDPOINT", raising=False)
        assert get_datarobot_url() == "https://app.datarobot.com"


# ---------------------------------------------------------------------------
# get_deployment_url
# ---------------------------------------------------------------------------


class TestGetDeploymentUrl:
    def test_uses_external_url(self, monkeypatch):
        monkeypatch.setenv("DATAROBOT_WEB_SERVER_URL", "https://dr.example.com")
        result = get_deployment_url("abc123")
        assert result == "https://dr.example.com/console-nextgen/deployments/abc123/"

    def test_fallback_base_url(self, monkeypatch):
        monkeypatch.delenv("DATAROBOT_WEB_SERVER_URL", raising=False)
        monkeypatch.delenv("DATAROBOT_API_TOKEN", raising=False)
        monkeypatch.setenv("DATAROBOT_ENDPOINT", "https://app.datarobot.com/api/v2")
        result = get_deployment_url("dep456")
        assert result == "https://app.datarobot.com/console-nextgen/deployments/dep456/"
