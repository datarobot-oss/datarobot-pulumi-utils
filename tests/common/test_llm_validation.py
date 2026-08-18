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
import builtins
from unittest.mock import MagicMock, patch

import pytest

from datarobot_pulumi_utils.common.llm_validation import (
    USE_GATEWAY_ENV_VAR,
    verify_llm,
    verify_llm_gateway_model_availability,
)
from datarobot_pulumi_utils.schema.llms import DEPLOYED_LLM_PLACEHOLDER_MODEL


def catalog_entry(model, *, llm_id=None, is_active=True, is_deprecated=False):
    return {
        "model": model,
        "llmId": llm_id or f"{model}-llm-id",
        "isActive": is_active,
        "isDeprecated": is_deprecated,
    }


@pytest.fixture
def mock_dr_client():
    """Patch datarobot.Client so the catalog route returns whatever a test assigns."""
    with patch("datarobot_pulumi_utils.common.llm_validation.datarobot.Client") as client_cls:
        client = client_cls.return_value
        client.endpoint = "https://app.datarobot.com/api/v2/"
        client.get.return_value.json.return_value = {"data": []}
        yield client


def set_catalog(mock_dr_client, entries):
    mock_dr_client.get.return_value.json.return_value = {"data": entries}


@pytest.fixture
def mock_completion():
    """Patch the deferred litellm import with a stub returning a valid completion."""
    completion = MagicMock(return_value={"choices": [{"message": {"content": "Hello"}}]})
    with patch("datarobot_pulumi_utils.common.llm_validation._load_completion", return_value=completion):
        yield completion


@pytest.fixture(autouse=True)
def clear_gateway_env(monkeypatch):
    monkeypatch.delenv(USE_GATEWAY_ENV_VAR, raising=False)


# --- verify_llm_gateway_model_availability ------------------------------------------------


def test_catalog_hit_by_model_name(mock_dr_client):
    # WHEN the model is in the catalog and active
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini"), catalog_entry("bedrock/nova-pro")])

    # THEN the check passes and queries the catalog route
    verify_llm_gateway_model_availability("azure/gpt-5-mini")
    mock_dr_client.get.assert_called_once_with("genai/llmgw/catalog/")


def test_catalog_hit_strips_unified_prefix(mock_dr_client):
    # WHEN given the unified datarobot/ form, the prefix must be stripped before matching
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini")])

    verify_llm_gateway_model_availability("datarobot/azure/gpt-5-mini")


def test_catalog_hit_by_llm_id(mock_dr_client):
    # WHEN the identifier matches llmId rather than model
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini", llm_id="azure-openai-gpt-5-mini")])

    verify_llm_gateway_model_availability("azure-openai-gpt-5-mini")


def test_catalog_miss_raises_and_lists_active_models(mock_dr_client):
    # WHEN the model is absent
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini"), catalog_entry("retired/model", is_active=False)])

    with pytest.raises(ValueError) as excinfo:
        verify_llm_gateway_model_availability("azure/nonexistent")

    message = str(excinfo.value)
    assert "not found in catalog" in message
    # THEN only active models are offered as alternatives
    assert "azure/gpt-5-mini" in message
    assert "retired/model" not in message


def test_catalog_miss_message_names_caller_override_points(mock_dr_client):
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini")])

    with pytest.raises(ValueError) as excinfo:
        verify_llm_gateway_model_availability(
            "azure/nonexistent",
            model_env_var="MY_APP_DEFAULT_MODEL",
            config_location="infra/configurations/my_app/",
        )

    message = str(excinfo.value)
    assert "MY_APP_DEFAULT_MODEL" in message
    assert "infra/configurations/my_app/" in message


def test_catalog_miss_message_omits_override_points_when_not_given(mock_dr_client):
    # The library does not know the caller's app name, so with no hints the message must
    # still be coherent rather than referencing an empty variable name.
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini")])

    with pytest.raises(ValueError) as excinfo:
        verify_llm_gateway_model_availability("azure/nonexistent")

    message = str(excinfo.value)
    assert "environment variable" not in message
    assert "Choose an active model" in message


def test_catalog_duplicate_match_raises(mock_dr_client):
    # WHEN two entries claim the same identifier, we cannot tell which one was meant
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-5-mini"), catalog_entry("azure/gpt-5-mini")])

    with pytest.raises(ValueError, match="Multiple models found"):
        verify_llm_gateway_model_availability("azure/gpt-5-mini")


def test_catalog_inactive_model_raises(mock_dr_client):
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-4", is_active=False)])

    with pytest.raises(ValueError, match="is not active or is retired"):
        verify_llm_gateway_model_availability("azure/gpt-4")


def test_catalog_deprecated_but_active_model_warns_and_passes(mock_dr_client, caplog):
    # WHEN the model is deprecated but still active, the deploy should proceed with a warning
    set_catalog(mock_dr_client, [catalog_entry("azure/gpt-4", is_deprecated=True, is_active=True)])

    with caplog.at_level("WARNING"):
        verify_llm_gateway_model_availability("azure/gpt-4")

    assert "deprecated but active" in caplog.text


# --- verify_llm ---------------------------------------------------------------------------


def test_verify_llm_deployment_routes_to_deployment_chat_endpoint(mock_dr_client, mock_completion):
    # WHEN a deployment id is given, the call goes to that deployment's chat endpoint
    verify_llm(model_id="azure/gpt-5-mini", deployment_id="abc123")

    kwargs = mock_completion.call_args.kwargs
    assert kwargs["api_base"] == "https://app.datarobot.com/api/v2/deployments/abc123/chat/completions"
    # The deployment routes by id, so the model string is a label -- sent in unified form.
    assert kwargs["model"] == "datarobot/azure/gpt-5-mini"


def test_verify_llm_deployment_without_model_uses_placeholder(mock_dr_client, mock_completion):
    verify_llm(deployment_id="abc123")

    assert mock_completion.call_args.kwargs["model"] == DEPLOYED_LLM_PLACEHOLDER_MODEL


def test_verify_llm_gateway_flag_sends_prefixed_model(mock_completion):
    # WHEN gateway routing is requested, LiteLLM needs the datarobot/ prefix
    verify_llm(model_id="azure/gpt-5-mini", use_llm_gateway=True)

    assert mock_completion.call_args.kwargs["model"] == "datarobot/azure/gpt-5-mini"
    assert "api_base" not in mock_completion.call_args.kwargs


@pytest.mark.parametrize("env_value", ["1", "true", "TRUE", "yes", "Yes"])
def test_verify_llm_gateway_env_var_enables_gateway(monkeypatch, mock_completion, env_value):
    monkeypatch.setenv(USE_GATEWAY_ENV_VAR, env_value)

    verify_llm(model_id="azure/gpt-5-mini")

    assert mock_completion.call_args.kwargs["model"] == "datarobot/azure/gpt-5-mini"


@pytest.mark.parametrize("env_value", ["", "0", "false", "no", "maybe"])
def test_verify_llm_non_truthy_env_var_keeps_external_provider_routing(monkeypatch, mock_completion, env_value):
    monkeypatch.setenv(USE_GATEWAY_ENV_VAR, env_value)

    verify_llm(model_id="datarobot/azure/gpt-5-mini")

    # THEN the prefix is stripped so LiteLLM addresses Azure directly
    assert mock_completion.call_args.kwargs["model"] == "azure/gpt-5-mini"


def test_verify_llm_external_provider_strips_prefix(mock_completion):
    verify_llm(model_id="datarobot/bedrock/nova-pro")

    assert mock_completion.call_args.kwargs["model"] == "bedrock/nova-pro"


def test_verify_llm_requires_model_or_deployment(mock_completion):
    with pytest.raises(ValueError, match="model_id must be provided"):
        verify_llm()


def test_verify_llm_empty_completion_raises():
    # A bare `assert` here would be stripped under `python -O`; the check must raise.
    completion = MagicMock(return_value={"choices": [{"message": {"content": ""}}]})
    with patch("datarobot_pulumi_utils.common.llm_validation._load_completion", return_value=completion):
        with pytest.raises(RuntimeError, match="empty completion"):
            verify_llm(model_id="azure/gpt-5-mini")


def test_verify_llm_malformed_completion_raises():
    completion = MagicMock(return_value={"choices": []})
    with patch("datarobot_pulumi_utils.common.llm_validation._load_completion", return_value=completion):
        with pytest.raises(RuntimeError, match="malformed completion response"):
            verify_llm(model_id="azure/gpt-5-mini")


def test_verify_llm_missing_litellm_raises_actionable_import_error(monkeypatch):
    # WHEN the optional extra is not installed
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "litellm":
            raise ImportError("No module named 'litellm'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError, match=r"datarobot-pulumi-utils\[llm\]"):
        verify_llm(model_id="azure/gpt-5-mini")
