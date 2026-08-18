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
"""Runtime parameter defaults for a custom model built from an LLM blueprint."""

from __future__ import annotations

import pulumi
import pulumi_datarobot


def get_blueprint_runtime_parameters(
    llm_blueprint_id: pulumi.Input[str],
    playground_id: pulumi.Input[str],
    llm_id: pulumi.Input[str],
) -> list[pulumi_datarobot.CustomModelRuntimeParameterValueArgs]:
    """Return the runtime parameters an LLM-blueprint custom model needs to load and serve.

    Creating a custom model from a blueprint with a *partial* ``runtime_parameter_values`` set
    makes the provider keep only the supplied parameters and drop every other blueprint default,
    including DRUM system parameters such as ``DEVICE_FOR_NEURAL_NETWORK_COMPUTATIONS`` that the
    model requires to load. We therefore restate the full default set here so callers can submit
    it explicitly (alongside their credential parameters) and never rely on a partial submission.
    """
    Arg = pulumi_datarobot.CustomModelRuntimeParameterValueArgs
    return [
        Arg(key="PROMPT_COLUMN_NAME", type="string", value="promptText"),
        Arg(key="LLM_BLUEPRINT_ID", type="string", value=llm_blueprint_id),
        Arg(key="LLM_BLUEPRINT_ID_COLUMN_NAME", type="string", value="LLM_BLUEPRINT_ID"),
        Arg(key="ENABLE_LLM_BLUEPRINT_ID_COLUMN", type="boolean", value="true"),
        Arg(key="LLM_ID", type="string", value=llm_id),
        Arg(key="PLAYGROUND_ID", type="string", value=playground_id),
        Arg(key="DEVICE_FOR_NEURAL_NETWORK_COMPUTATIONS", type="string", value="cpu"),
        Arg(key="CUSTOM_MODEL_WORKERS", type="numeric", value="1"),
        Arg(key="DRUM_SERVER_TYPE", type="string", value="gunicorn"),
        Arg(key="DRUM_GUNICORN_WORKER_CLASS", type="string", value="sync"),
        Arg(key="DRUM_WORKER_CONNECTIONS", type="numeric", value="100"),
        Arg(key="DRUM_CLIENT_REQUEST_TIMEOUT", type="numeric", value="300"),
    ]
