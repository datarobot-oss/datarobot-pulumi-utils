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
"""Pre-deploy smoke checks for an LLM configuration.

These helpers talk to the DataRobot API and (for :func:`verify_llm`) to the LLM itself.
They create no Pulumi resources, so they are safe to call from anywhere in a Pulumi
program -- including before any resource is declared, which is the point: fail on a
misconfigured model before spending a deploy on it.

:func:`verify_llm` needs `litellm`, which is an optional dependency of this package::

    pip install "datarobot-pulumi-utils[llm]"
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

import datarobot

from datarobot_pulumi_utils.schema.llms import DEPLOYED_LLM_PLACEHOLDER_MODEL, ensure_datarobot_prefix

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)

LLM_GATEWAY_CATALOG_ROUTE = "genai/llmgw/catalog/"

# Environment variable that turns on LLM Gateway routing when `use_llm_gateway` is not passed
# explicitly. Same variable datarobot-genai reads at runtime, so a check here matches the
# routing the deployed app will do.
USE_GATEWAY_ENV_VAR = "USE_DATAROBOT_LLM_GATEWAY"
_TRUTHY = frozenset({"1", "true", "yes"})


def _load_completion() -> Callable[..., Any]:
    """Import `litellm.completion` on demand, with an actionable error if it is missing.

    `litellm` is a heavy dependency and only :func:`verify_llm` needs it, so it is an
    optional extra rather than a base requirement and is imported at call time.
    """
    try:
        from litellm import completion
    except ImportError as exc:  # pragma: no cover - exercised via monkeypatched import
        raise ImportError(
            "verify_llm() requires the 'litellm' package, which is an optional dependency of "
            "datarobot-pulumi-utils. Install it with: pip install 'datarobot-pulumi-utils[llm]'"
        ) from exc

    # litellm ships no type information, so `completion` arrives as Any; pin it to the
    # callable shape we rely on rather than leaking Any to callers.
    completion_fn: Callable[..., Any] = completion
    return completion_fn


def _require_nonempty_completion(response: Any, model: str) -> None:
    """Raise unless the completion came back with non-empty assistant content.

    The source implementation used a bare `assert`, which is stripped under `python -O` and
    would silently turn a failed smoke check into a passing one.
    """
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Model '{model}' returned a malformed completion response: {response!r}") from exc

    if not content:
        raise RuntimeError(
            f"Model '{model}' is reachable but returned an empty completion. "
            "Check the model's credentials, quota, and content filters."
        )


def verify_llm_gateway_model_availability(
    model_id: str,
    *,
    model_env_var: str | None = None,
    config_location: str | None = None,
) -> None:
    """Verify `model_id` is present and active in this cluster's LLM Gateway catalog.

    Parameters
    ----------
    model_id:
        Gateway model string, with or without the unified ``datarobot/`` prefix.
    model_env_var:
        Name of the environment variable a caller can set to override the model, quoted in
        the remediation message on a catalog miss (e.g. ``"MY_APP_DEFAULT_MODEL"``).
    config_location:
        Where the caller's default model is declared, quoted in the same message
        (e.g. ``"infra/configurations/my_app/"``).

    Raises
    ------
    ValueError
        If the model is absent from the catalog, ambiguous, or inactive/retired.
    """
    model_id = model_id.removeprefix("datarobot/")

    dr_client = datarobot.Client()
    response = dr_client.get(LLM_GATEWAY_CATALOG_ROUTE)
    data = response.json()

    active_models_display = "\n.   - ".join(model["model"] for model in data["data"] if model["isActive"])
    matched_models = [model for model in data["data"] if (model["model"] == model_id or model["llmId"] == model_id)]

    if not matched_models:
        raise ValueError(_catalog_miss_message(model_id, active_models_display, model_env_var, config_location))

    if len(matched_models) != 1:
        raise ValueError(f"Multiple models found for '{model_id}' in catalog. {matched_models}")

    if matched_models[0]["isDeprecated"] and matched_models[0]["isActive"]:
        log.warning(
            """Model '%s' is deprecated but active. The end of support date falls within 90 days.
            It is recommended that you choose a different model, where possible.

            Available models: %s""",
            model_id,
            active_models_display,
        )

    if not matched_models[0]["isActive"]:
        raise ValueError(f"Model '{model_id}' is not active or is retired. Available models: {active_models_display}")


def _catalog_miss_message(
    model_id: str,
    active_models_display: str,
    model_env_var: str | None,
    config_location: str | None,
) -> str:
    """Build the catalog-miss error, naming the caller's override points when known."""
    remediations = []
    if model_env_var:
        remediations.append(f"set the environment variable '{model_env_var}' to an active model")
    if config_location:
        remediations.append(f"edit `default_model` in the active configuration module under {config_location}")

    if remediations:
        how_to_change = "To change the default model, " + ", or ".join(remediations) + "."
        multiple_configs = (
            "\n\n        If you have multiple Pulumi LLM configurations, change the one you want to "
            "modify -- each has its own override."
        )
    else:
        how_to_change = "Choose an active model from the list below."
        multiple_configs = ""

    return f"""
        Model '{model_id}' not found in catalog. Model availability may vary depending on
        region and organization settings.

        {how_to_change}{multiple_configs}

        Available models: {active_models_display}
        """


def verify_llm(
    model_id: str | None = None,
    deployment_id: str | None = None,
    use_llm_gateway: bool = False,
) -> None:
    """Verify the configured LLM is reachable and can say hello before we deploy.

    This mirrors how datarobot-genai's ``get_llm()`` routes, so a successful check here means
    the app will route the same way at runtime:

    - Deployment (``deployment_id`` set): call the deployment's chat endpoint. The deployment
      routes by ID, so the model string is only a label; send it in the unified ``datarobot/``
      form (falling back to the inert placeholder).
    - LLM Gateway (``use_llm_gateway`` or ``USE_DATAROBOT_LLM_GATEWAY`` truthy): send a
      ``datarobot/``-prefixed model so LiteLLM uses the DataRobot provider.
    - External provider: strip the ``datarobot/`` prefix so LiteLLM calls the provider directly
      (``azure/...``, ``bedrock/...``) using the credentials in the environment.

    Raises
    ------
    ImportError
        If the optional ``litellm`` dependency is not installed.
    ValueError
        If neither ``model_id`` nor ``deployment_id`` is given.
    RuntimeError
        If the model responds with an empty or malformed completion.
    """
    completion = _load_completion()

    # Pre-existing / managed DataRobot deployment: routes by deployment ID.
    if deployment_id:
        dr_client = datarobot.Client()
        deployment_chat_base_url = f"{dr_client.endpoint.rstrip('/')}/deployments/{deployment_id}/chat/completions"
        model = ensure_datarobot_prefix(model_id or DEPLOYED_LLM_PLACEHOLDER_MODEL)
        response = completion(
            model=model,
            messages=[{"content": "Hi", "role": "user"}],
            api_base=deployment_chat_base_url,
        )
        _require_nonempty_completion(response, model)
        return

    if model_id is None:
        raise ValueError("model_id must be provided to verify_llm")

    use_llm_gateway_enabled = use_llm_gateway or os.environ.get(USE_GATEWAY_ENV_VAR, "").lower() in _TRUTHY

    if use_llm_gateway_enabled:
        # Gateway: LiteLLM routes to the DataRobot provider on the datarobot/ prefix.
        model = ensure_datarobot_prefix(model_id)
    else:
        # External provider: LiteLLM must address the provider directly (azure/..., bedrock/...).
        model = model_id.removeprefix("datarobot/")

    response = completion(
        model=model,
        messages=[{"content": "Hi", "role": "user"}],
    )
    _require_nonempty_completion(response, model)
