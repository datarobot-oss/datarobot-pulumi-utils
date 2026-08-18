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
"""DataRobot credential resources for an externally-hosted LLM.

Given a gateway model string this module works out which provider serves it, creates the
DataRobot credential resources that provider needs (API token, AWS, or Google Cloud), and
returns the custom-model runtime parameter values that reference them.

Unlike :mod:`datarobot_pulumi_utils.common.llm_validation`, calling
:func:`get_runtime_values` **declares Pulumi resources**, so it belongs inside a Pulumi
program.
"""

from __future__ import annotations

import logging
import os
import tempfile
from dataclasses import dataclass, field
from typing import Literal, NamedTuple

import pulumi
import pulumi_datarobot

log = logging.getLogger(__name__)

RuntimeParameterType = Literal["string", "credential", "google_credential", "aws_credential"]


class RuntimeParameterValueArgs(NamedTuple):
    """A runtime parameter a provider needs, before its value is resolved from the environment."""

    key: str
    type: RuntimeParameterType
    default: str | None = None


@dataclass(frozen=True)
class ProviderCredential:
    """How to source and materialise the credentials for one LLM provider."""

    # The provider: azure, bedrock, etc.
    provider: str
    # The environment variable suffixes for the credentials needed by the provider. Combined
    # with `prefix_list`: we look for the first prefix that has the variable set and copy the
    # value to the others. Providers with an empty `prefix_list` are never cross-populated --
    # their variables are already fully-qualified names read directly from the environment.
    env_vars: tuple[str, ...] = field(default_factory=tuple)
    # The possible prefixes that both DataRobot Pulumi need and LiteLLM needs
    prefix_list: tuple[str, ...] = field(default_factory=tuple)
    runtime_parameters: tuple[RuntimeParameterValueArgs, ...] = field(default_factory=tuple)

    def hydrate_env(self) -> None:
        """Cross-populate this provider's credential variables in ``os.environ``.

        Copies the first value found across ``prefix_list`` to every other prefix that is
        unset -- e.g. ``OPENAI_API_KEY`` to ``AZURE_API_KEY`` -- and converts between
        Google's file-path and JSON-string credential forms.

        This mutates process state and is therefore explicit: the provider map used to do
        this in ``__post_init__``, which meant merely *importing* the module cross-populated
        every provider's variables and wrote a temp file for
        ``GOOGLE_APPLICATION_CREDENTIALS``. Tolerable in a per-project module, not in a
        published library.
        """
        for var_name in self.env_vars:
            # Find the first existing variable across all prefixes
            found_value = None
            for prefix in self.prefix_list:
                full_var_name = f"{prefix}{var_name}"
                if full_var_name in os.environ:
                    found_value = os.environ[full_var_name]
                    break
            if not found_value:
                continue

            # Special handling for Google credentials
            if var_name == "_APPLICATION_CREDENTIALS":
                # GOOGLE_APPLICATION_CREDENTIALS is a file path, need to read and set
                # GOOGLE_SERVICE_ACCOUNT as JSON string
                try:
                    with open(found_value, "r") as f:
                        json_content = f.read()
                except OSError:
                    continue  # If file isn't readable, skip cross-population
                if "GOOGLE_SERVICE_ACCOUNT" not in os.environ:
                    os.environ["GOOGLE_SERVICE_ACCOUNT"] = json_content
                continue

            if var_name == "_SERVICE_ACCOUNT":
                # GOOGLE_SERVICE_ACCOUNT is a JSON string, need to create file and set
                # GOOGLE_APPLICATION_CREDENTIALS
                try:
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
                        temp_file.write(found_value)
                except OSError:
                    log.exception("Failed to create temp file for GOOGLE_APPLICATION_CREDENTIALS")
                    continue
                if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file.name
                continue

            # Copy the found value to all missing combinations
            for prefix in self.prefix_list:
                full_var_name = f"{prefix}{var_name}"
                if full_var_name not in os.environ:
                    os.environ[full_var_name] = found_value

    def runtime_parameter_values(
        self, resource_suffix: str
    ) -> list[pulumi_datarobot.CustomModelRuntimeParameterValueArgs]:
        """Create this provider's credential resources and return the runtime parameters.

        ``resource_suffix`` is appended to every credential's ``resource_name``. Changing it
        renames the resources, which makes ``pulumi up`` replace live credentials -- see
        :func:`get_runtime_values`.
        """
        runtime_values: list[pulumi_datarobot.CustomModelRuntimeParameterValueArgs] = []
        credential: (
            pulumi_datarobot.ApiTokenCredential
            | pulumi_datarobot.GoogleCloudCredential
            | pulumi_datarobot.AwsCredential
        )
        for param in self.runtime_parameters:
            resource_name = f"{pulumi.get_project()} {param.key} {resource_suffix}"
            if param.type == "string":
                runtime_values.append(
                    pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
                        key=param.key,
                        type=param.type,
                        value=os.environ.get(param.key) or param.default or "",
                    )
                )
            elif param.type == "credential":
                credential = pulumi_datarobot.ApiTokenCredential(
                    resource_name=resource_name,
                    api_token=os.environ.get(param.key),
                )
                runtime_values.append(
                    pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
                        key=param.key, type="credential", value=credential.id
                    )
                )
            elif param.type == "google_credential":
                credential = pulumi_datarobot.GoogleCloudCredential(
                    resource_name=resource_name,
                    gcp_key=os.environ.get(param.key),
                )
                runtime_values.append(
                    pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
                        key=param.key,
                        type="credential",
                        value=credential.id,
                    )
                )
            elif param.type == "aws_credential":
                credential = pulumi_datarobot.AwsCredential(
                    resource_name=resource_name,
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                    aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
                )
                runtime_values.append(
                    pulumi_datarobot.CustomModelRuntimeParameterValueArgs(
                        key=param.key,
                        type="credential",
                        value=credential.id,
                    )
                )
        return runtime_values


# Provider definitions are inert data: constructing them touches nothing outside the object,
# because env cross-population lives in the explicit `hydrate_env()`. Importing this module
# therefore has no side effects.
PROVIDER_CREDENTIALS_MAP: dict[str, ProviderCredential] = {
    # Generic OpenAI-compatible endpoint (Nebius, Groq, xAI, DeepSeek, self-hosted vLLM, ...).
    # Only api_base + api_key: NO OPENAI_API_DEPLOYMENT_ID. deployment_id is an Azure-only concept
    # and forwarding it makes LiteLLM rewrite the call as an Azure
    # /openai/deployments/<id>/chat/completions request that non-Azure providers 404. This is the
    # fallback for any provider not explicitly listed below (see get_runtime_values).
    "openai": ProviderCredential(
        provider="openai",
        env_vars=("_API_KEY", "_API_BASE"),
        prefix_list=("OPENAI",),
        runtime_parameters=(
            RuntimeParameterValueArgs(key="OPENAI_API_KEY", type="credential"),
            RuntimeParameterValueArgs(key="OPENAI_API_BASE", type="string"),
        ),
    ),
    # The "Big Three" Cloud Providers
    # Azure is OpenAI-compatible but additionally addressed by an Azure deployment name, so it is
    # the one provider that also carries OPENAI_API_DEPLOYMENT_ID (and an api version).
    "azure": ProviderCredential(
        provider="azure",
        env_vars=("_API_KEY", "_API_BASE", "_API_VERSION", "_API_DEPLOYMENT_ID"),
        prefix_list=("OPENAI", "AZURE"),
        runtime_parameters=(
            RuntimeParameterValueArgs(key="OPENAI_API_KEY", type="credential"),
            RuntimeParameterValueArgs(key="OPENAI_API_BASE", type="string"),
            RuntimeParameterValueArgs(key="OPENAI_API_VERSION", type="string", default="2024-08-01-preview"),
            RuntimeParameterValueArgs(key="OPENAI_API_DEPLOYMENT_ID", type="string"),
        ),
    ),
    "bedrock": ProviderCredential(
        provider="bedrock",
        env_vars=("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION_NAME"),
        runtime_parameters=(
            RuntimeParameterValueArgs(key="AWS_ACCOUNT", type="aws_credential"),
            RuntimeParameterValueArgs(key="AWS_REGION_NAME", type="string", default="us-east-1"),
        ),
    ),
    "vertex_ai": ProviderCredential(
        provider="vertex_ai",
        env_vars=("_APPLICATION_CREDENTIALS", "_SERVICE_ACCOUNT"),
        prefix_list=("VERTEXAI", "GOOGLE"),
        runtime_parameters=(
            RuntimeParameterValueArgs(key="GOOGLE_SERVICE_ACCOUNT", type="google_credential"),
            RuntimeParameterValueArgs(key="GOOGLE_REGION", type="string", default="us-west1"),
        ),
    ),
    "anthropic": ProviderCredential(
        provider="anthropic",
        env_vars=("ANTHROPIC_API_KEY",),
        runtime_parameters=(RuntimeParameterValueArgs(key="ANTHROPIC_API_KEY", type="credential"),),
    ),
    "cohere": ProviderCredential(
        provider="cohere",
        env_vars=("COHERE_API_KEY",),
        runtime_parameters=(RuntimeParameterValueArgs(key="COHERE_API_KEY", type="credential"),),
    ),
    "togetherai": ProviderCredential(
        provider="togetherai",
        env_vars=("TOGETHERAI_API_KEY",),
        runtime_parameters=(RuntimeParameterValueArgs(key="TOGETHERAI_API_KEY", type="credential"),),
    ),
}

# Map common aliases to their canonical provider names
PROVIDER_ALIASES = {"amazon": "bedrock", "google": "vertex_ai"}

# Any provider without explicit handling (nebius, groq, xai, deepseek, ...) is treated as a
# generic OpenAI-compatible endpoint: api_base + api_key, no Azure-only deployment_id.
FALLBACK_PROVIDER = "openai"


def resolve_provider_credential(model_id: str) -> ProviderCredential:
    """Work out which provider serves ``model_id`` and return its credential definition.

    Accepts a gateway model string with or without the unified ``datarobot/`` prefix, in
    either the slash (``azure/gpt-5-mini``) or legacy dash (``azure-openai-gpt-5-mini``)
    format. Unrecognised providers fall back to the generic OpenAI-compatible definition.
    """
    # Provider drives credential selection. Strip the unified datarobot/ prefix first so
    # provider parsing sees e.g. "azure/..." not "datarobot/azure/...".
    model_id = model_id.removeprefix("datarobot/")
    # Extract provider from model_id - try slash first (new format), then dash (legacy format)
    if "/" in model_id:
        provider = model_id.split("/")[0]
    elif "-" in model_id:
        provider = model_id.split("-")[0]
    else:
        provider = model_id
    provider = PROVIDER_ALIASES.get(provider, provider)
    return PROVIDER_CREDENTIALS_MAP.get(provider, PROVIDER_CREDENTIALS_MAP[FALLBACK_PROVIDER])


def get_runtime_values(
    model_id: str, *, resource_suffix: str
) -> list[pulumi_datarobot.CustomModelRuntimeParameterValueArgs]:
    """Create the credential resources ``model_id``'s provider needs and return its runtime values.

    Parameters
    ----------
    model_id:
        Gateway model string, with or without the unified ``datarobot/`` prefix.
    resource_suffix:
        Appended to each credential's ``resource_name``, which is
        ``f"{pulumi.get_project()} {key} {resource_suffix}"``. Required, and keyword-only,
        because the resource name is part of Pulumi's resource identity: changing it makes
        ``pulumi up`` **replace** the live credentials of every deployed stack. Callers
        migrating off a per-project ``libllm.py`` must pass the bracketed app name they
        used before, e.g. ``resource_suffix="[my-app]"``.
    """
    credential = resolve_provider_credential(model_id)
    # Only the selected provider is hydrated. The previous module-level map hydrated every
    # provider as an import side effect, which could cross-populate variables for providers
    # the program never uses.
    credential.hydrate_env()
    return credential.runtime_parameter_values(resource_suffix)
