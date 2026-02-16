# Copyright 2026 DataRobot, Inc.
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
from datarobot.enums import EXECUTION_ENVIRONMENT_VERSION_BUILD_STATUS
from datarobot.errors import ClientError

from datarobot_pulumi_utils.pulumi.execution_environment import resolve_execution_environment_version


@pytest.fixture(autouse=True)
def mock_pulumi():
    with patch("datarobot_pulumi_utils.pulumi.execution_environment.pulumi") as m:
        yield m


@pytest.fixture(autouse=True)
def mock_dr():
    with patch("datarobot_pulumi_utils.pulumi.execution_environment.dr") as m:
        m.errors.ClientError = ClientError
        yield m


@pytest.mark.parametrize(
    "env_value",
    [None, "", "short", "not24hex!!!!!!!!!!!!!!!!", "ABCDEF0123456789abcdef01"],
)
def test_invalid_or_unset_env_returns_none_without_api_call(monkeypatch, mock_pulumi, mock_dr, env_value):
    # WHEN env is unset or version id is invalid (wrong format/length/case)
    if env_value is None:
        monkeypatch.delenv("EE_VERSION_VAR", raising=False)
    else:
        monkeypatch.setenv("EE_VERSION_VAR", env_value)

    result = resolve_execution_environment_version("ee-id", "EE_VERSION_VAR")

    # THEN no API call, info "using latest", return None
    assert result is None
    mock_dr.ExecutionEnvironmentVersion.get.assert_not_called()
    mock_pulumi.info.assert_called_once()
    assert "using latest" in mock_pulumi.info.call_args[0][0]


def test_valid_hex_with_quotes_stripped(monkeypatch, mock_pulumi, mock_dr):
    # WHEN env version var has a valid value wrapped in quotes and the env is available
    monkeypatch.setenv("EE_VERSION_VAR", "'abcdef0123456789abcdef01'")
    mock_version = MagicMock()
    mock_version.id = "abcdef0123456789abcdef01"
    mock_version.build_status = EXECUTION_ENVIRONMENT_VERSION_BUILD_STATUS.SUCCESS
    mock_dr.ExecutionEnvironmentVersion.get.return_value = mock_version

    result = resolve_execution_environment_version("ee-id", "EE_VERSION_VAR")

    # THEN return version id (quotes stripped)
    assert result == "abcdef0123456789abcdef01"
    mock_pulumi.warn.assert_not_called()


def test_version_found_and_success_returns_id(monkeypatch, mock_pulumi, mock_dr):
    # WHEN pinned version exists and build_status is SUCCESS
    monkeypatch.setenv("EE_VERSION_VAR", "abcdef0123456789abcdef01")
    mock_version = MagicMock()
    mock_version.id = "abcdef0123456789abcdef01"
    mock_version.build_status = EXECUTION_ENVIRONMENT_VERSION_BUILD_STATUS.SUCCESS
    mock_dr.ExecutionEnvironmentVersion.get.return_value = mock_version

    result = resolve_execution_environment_version("ee-id", "EE_VERSION_VAR")

    # THEN return that version id
    assert result == "abcdef0123456789abcdef01"
    mock_pulumi.warn.assert_not_called()


def test_version_not_found_client_error_returns_none(monkeypatch, mock_pulumi, mock_dr):
    # WHEN get() raises ClientError (e.g. version missing on this env)
    monkeypatch.setenv("EE_VERSION_VAR", "a1b2c3d4e5f6071829364455")
    mock_dr.ExecutionEnvironmentVersion.get.side_effect = ClientError("Not found", 404)

    result = resolve_execution_environment_version("ee-id", "EE_VERSION_VAR")

    # THEN warn "using latest", return None
    assert result is None
    mock_pulumi.warn.assert_called_once()
    call_msg = mock_pulumi.warn.call_args[0][0]
    assert "a1b2c3d4e5f6071829364455" in call_msg
    assert "using latest" in call_msg


def test_version_build_not_success_returns_none(monkeypatch, mock_pulumi, mock_dr):
    # WHEN version exists but build_status is not SUCCESS
    monkeypatch.setenv("EE_VERSION_VAR", "abcdef0123456789abcdef01")
    mock_version = MagicMock()
    mock_version.id = "abcdef0123456789abcdef01"
    mock_version.build_status = "processing"
    mock_dr.ExecutionEnvironmentVersion.get.return_value = mock_version

    result = resolve_execution_environment_version("ee-id", "EE_VERSION_VAR")

    # THEN warn "using latest", return None
    assert result is None
    mock_pulumi.warn.assert_called_once()
    call_msg = mock_pulumi.warn.call_args[0][0]
    assert "abcdef0123456789abcdef01" in call_msg
    assert "using latest" in call_msg
