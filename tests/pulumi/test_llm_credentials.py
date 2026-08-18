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
import json
import os
from unittest.mock import patch

import pytest

from datarobot_pulumi_utils.pulumi.llm_credentials import (
    PROVIDER_CREDENTIALS_MAP,
    ProviderCredential,
    RuntimeParameterValueArgs,
    get_runtime_values,
    resolve_provider_credential,
)

PROJECT_NAME = "my-project"

# Every credential variable any provider in the map reads, so a test can start from a clean
# environment and not inherit the developer's real credentials.
CREDENTIAL_ENV_VARS = [
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "OPENAI_API_VERSION",
    "OPENAI_API_DEPLOYMENT_ID",
    "AZURE_API_KEY",
    "AZURE_API_BASE",
    "AZURE_API_VERSION",
    "AZURE_API_DEPLOYMENT_ID",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_REGION_NAME",
    "AWS_ACCOUNT",
    "GOOGLE_SERVICE_ACCOUNT",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_REGION",
    "VERTEXAI_SERVICE_ACCOUNT",
    "VERTEXAI_APPLICATION_CREDENTIALS",
    "ANTHROPIC_API_KEY",
    "COHERE_API_KEY",
    "TOGETHERAI_API_KEY",
]


@pytest.fixture(autouse=True)
def clean_credential_env(monkeypatch):
    for var in CREDENTIAL_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def mock_pulumi():
    """Stand in for the Pulumi runtime: fix the project name and record credential resources."""
    with (
        patch("datarobot_pulumi_utils.pulumi.llm_credentials.pulumi") as mock_pulumi_mod,
        patch("datarobot_pulumi_utils.pulumi.llm_credentials.pulumi_datarobot") as mock_provider,
    ):
        mock_pulumi_mod.get_project.return_value = PROJECT_NAME
        # CustomModelRuntimeParameterValueArgs is a plain args bag; keep the kwargs visible.
        mock_provider.CustomModelRuntimeParameterValueArgs.side_effect = lambda **kwargs: kwargs
        yield mock_provider


def args_by_key(runtime_values):
    return {value["key"]: value for value in runtime_values}


# --- provider resolution ------------------------------------------------------------------


@pytest.mark.parametrize(
    "model_id,expected_provider",
    [
        # Slash format (current).
        ("azure/gpt-5-mini", "azure"),
        ("bedrock/anthropic.claude-opus-4-5", "bedrock"),
        ("vertex_ai/gemini-2.5-pro", "vertex_ai"),
        ("anthropic/claude-opus-4-5", "anthropic"),
        # Dash format (legacy playground-style ids).
        ("azure-openai-gpt-5-mini", "azure"),
        ("cohere-command-r", "cohere"),
        ("togetherai-mistral-7b-instruct", "togetherai"),
        # Aliases.
        ("amazon-nova-pro", "bedrock"),
        ("amazon/nova-pro", "bedrock"),
        ("google/gemini-2.5-pro", "vertex_ai"),
        ("google-gemini-2.5-pro", "vertex_ai"),
        # The unified datarobot/ prefix must be stripped before parsing.
        ("datarobot/azure/gpt-5-mini", "azure"),
        ("datarobot/bedrock/nova-pro", "bedrock"),
        # No separator at all.
        ("openai", "openai"),
        # Unknown providers fall back to the generic OpenAI-compatible definition.
        ("nebius/llama-3.3-70b", "openai"),
        ("groq/llama-3.3-70b", "openai"),
        ("xai-grok-4", "openai"),
        ("somemodel", "openai"),
    ],
)
def test_resolve_provider_credential(model_id, expected_provider):
    assert resolve_provider_credential(model_id).provider == expected_provider


def test_datarobot_prefix_alone_does_not_select_a_provider():
    # "datarobot/azure/..." must resolve as azure, not as a "datarobot" provider; the prefix
    # is stripped before parsing, which this asserts from the other direction.
    assert resolve_provider_credential("datarobot/nebius/model").provider == "openai"


def test_importing_the_module_does_not_touch_the_environment():
    # The whole point of moving cross-population into hydrate_env(): the provider map is
    # inert data, so building it must not populate credentials for providers nobody uses.
    assert "AZURE_API_KEY" not in os.environ
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ
    assert all(isinstance(cred, ProviderCredential) for cred in PROVIDER_CREDENTIALS_MAP.values())


# --- resource naming (compatibility) ------------------------------------------------------


def test_resource_name_is_byte_identical_to_the_pre_migration_format(mock_pulumi):
    # HARD REQUIREMENT: the emitted resource_name must match what the per-project libllm.py
    # produced -- f"{pulumi.get_project()} {param.key} [{llm_app_name}]". Any drift makes
    # `pulumi up` REPLACE the live credentials of every deployed stack.
    llm_app_name = "my-llm-app"

    get_runtime_values("azure/gpt-5-mini", resource_suffix=f"[{llm_app_name}]")

    assert (
        mock_pulumi.ApiTokenCredential.call_args.kwargs["resource_name"]
        == f"{PROJECT_NAME} OPENAI_API_KEY [{llm_app_name}]"
    )


def test_resource_suffix_is_required_and_keyword_only():
    # A default would silently rename resources for a caller who forgot to pass it.
    with pytest.raises(TypeError):
        get_runtime_values("azure/gpt-5-mini")

    with pytest.raises(TypeError):
        get_runtime_values("azure/gpt-5-mini", "[my-llm-app]")


@pytest.mark.parametrize(
    "model_id,credential_attr,expected_key",
    [
        ("azure/gpt-5-mini", "ApiTokenCredential", "OPENAI_API_KEY"),
        ("bedrock/nova-pro", "AwsCredential", "AWS_ACCOUNT"),
        ("vertex_ai/gemini-2.5-pro", "GoogleCloudCredential", "GOOGLE_SERVICE_ACCOUNT"),
    ],
)
def test_resource_name_format_for_every_credential_type(mock_pulumi, model_id, credential_attr, expected_key):
    get_runtime_values(model_id, resource_suffix="[app]")

    resource = getattr(mock_pulumi, credential_attr)
    assert resource.call_args.kwargs["resource_name"] == f"{PROJECT_NAME} {expected_key} [app]"


# --- per-credential-type argument construction --------------------------------------------


def test_azure_builds_api_token_credential_and_string_params(monkeypatch, mock_pulumi):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    monkeypatch.setenv("OPENAI_API_BASE", "https://example.openai.azure.com")
    monkeypatch.setenv("OPENAI_API_DEPLOYMENT_ID", "my-deployment")

    values = args_by_key(get_runtime_values("azure/gpt-5-mini", resource_suffix="[app]"))

    # The API key becomes a credential resource, referenced by id.
    assert mock_pulumi.ApiTokenCredential.call_args.kwargs["api_token"] == "secret-key"
    assert values["OPENAI_API_KEY"]["type"] == "credential"
    assert values["OPENAI_API_KEY"]["value"] is mock_pulumi.ApiTokenCredential.return_value.id
    # String params are passed through verbatim.
    assert values["OPENAI_API_BASE"] == {
        "key": "OPENAI_API_BASE",
        "type": "string",
        "value": "https://example.openai.azure.com",
    }
    assert values["OPENAI_API_DEPLOYMENT_ID"]["value"] == "my-deployment"
    # Unset string params fall back to their declared default.
    assert values["OPENAI_API_VERSION"]["value"] == "2024-08-01-preview"


def test_unset_string_param_without_default_becomes_empty_string(mock_pulumi):
    values = args_by_key(get_runtime_values("azure/gpt-5-mini", resource_suffix="[app]"))

    assert values["OPENAI_API_BASE"]["value"] == ""


def test_openai_fallback_omits_azure_only_deployment_id(mock_pulumi):
    # deployment_id is Azure-only: forwarding it makes LiteLLM rewrite the call as an Azure
    # /openai/deployments/<id>/... request that non-Azure providers 404.
    values = args_by_key(get_runtime_values("nebius/llama-3.3-70b", resource_suffix="[app]"))

    assert set(values) == {"OPENAI_API_KEY", "OPENAI_API_BASE"}


def test_bedrock_builds_aws_credential_from_the_aws_env_vars(monkeypatch, mock_pulumi):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "akid")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "token")

    values = args_by_key(get_runtime_values("bedrock/nova-pro", resource_suffix="[app]"))

    kwargs = mock_pulumi.AwsCredential.call_args.kwargs
    assert kwargs["aws_access_key_id"] == "akid"
    assert kwargs["aws_secret_access_key"] == "secret"
    assert kwargs["aws_session_token"] == "token"
    # The runtime parameter type is plain "credential" even though the resource is AWS-specific.
    assert values["AWS_ACCOUNT"]["type"] == "credential"
    assert values["AWS_REGION_NAME"]["value"] == "us-east-1"


def test_vertex_ai_builds_google_credential_from_the_service_account_json(monkeypatch, mock_pulumi):
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT", '{"type": "service_account"}')

    values = args_by_key(get_runtime_values("vertex_ai/gemini-2.5-pro", resource_suffix="[app]"))

    assert mock_pulumi.GoogleCloudCredential.call_args.kwargs["gcp_key"] == '{"type": "service_account"}'
    assert values["GOOGLE_SERVICE_ACCOUNT"]["type"] == "credential"
    assert values["GOOGLE_REGION"]["value"] == "us-west1"


# --- hydrate_env --------------------------------------------------------------------------


def test_hydrate_env_cross_populates_across_prefixes(monkeypatch):
    # WHEN only the AZURE-prefixed variable is set, the OPENAI-prefixed one must be filled in,
    # because that is the key the runtime parameters actually read.
    monkeypatch.setenv("AZURE_API_KEY", "from-azure")

    PROVIDER_CREDENTIALS_MAP["azure"].hydrate_env()

    assert os.environ["OPENAI_API_KEY"] == "from-azure"


def test_hydrate_env_prefers_the_first_prefix_and_never_overwrites(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "from-openai")
    monkeypatch.setenv("AZURE_API_KEY", "from-azure")

    PROVIDER_CREDENTIALS_MAP["azure"].hydrate_env()

    # OPENAI comes first in prefix_list and both are already set, so nothing changes.
    assert os.environ["OPENAI_API_KEY"] == "from-openai"
    assert os.environ["AZURE_API_KEY"] == "from-azure"


def test_hydrate_env_is_called_for_the_selected_provider(monkeypatch, mock_pulumi):
    # End to end: an AZURE-only environment must still produce a populated credential.
    monkeypatch.setenv("AZURE_API_KEY", "from-azure")

    get_runtime_values("azure/gpt-5-mini", resource_suffix="[app]")

    assert mock_pulumi.ApiTokenCredential.call_args.kwargs["api_token"] == "from-azure"


def test_hydrate_env_google_service_account_json_becomes_a_credentials_file(monkeypatch, tmp_path):
    # GOOGLE_SERVICE_ACCOUNT (JSON string) -> GOOGLE_APPLICATION_CREDENTIALS (file path)
    payload = '{"type": "service_account", "project_id": "p"}'
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT", payload)

    PROVIDER_CREDENTIALS_MAP["vertex_ai"].hydrate_env()

    written_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    assert json.loads(open(written_path).read()) == json.loads(payload)


def test_hydrate_env_google_credentials_file_becomes_service_account_json(monkeypatch, tmp_path):
    # GOOGLE_APPLICATION_CREDENTIALS (file path) -> GOOGLE_SERVICE_ACCOUNT (JSON string)
    payload = '{"type": "service_account", "project_id": "p"}'
    key_file = tmp_path / "key.json"
    key_file.write_text(payload)
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(key_file))

    PROVIDER_CREDENTIALS_MAP["vertex_ai"].hydrate_env()

    assert os.environ["GOOGLE_SERVICE_ACCOUNT"] == payload


def test_hydrate_env_ignores_an_unreadable_google_credentials_file(monkeypatch, tmp_path):
    # A stale GOOGLE_APPLICATION_CREDENTIALS path must not crash the Pulumi program.
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(tmp_path / "missing.json"))

    PROVIDER_CREDENTIALS_MAP["vertex_ai"].hydrate_env()

    assert "GOOGLE_SERVICE_ACCOUNT" not in os.environ


def test_hydrate_env_is_a_noop_for_providers_without_prefixes(monkeypatch):
    # bedrock/anthropic/cohere/togetherai declare fully-qualified variable names and no
    # prefix list, so there is nothing to cross-populate.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")

    PROVIDER_CREDENTIALS_MAP["anthropic"].hydrate_env()

    assert os.environ["ANTHROPIC_API_KEY"] == "secret"


def test_runtime_parameter_value_args_defaults_to_no_default():
    param = RuntimeParameterValueArgs(key="OPENAI_API_KEY", type="credential")

    assert param.default is None
