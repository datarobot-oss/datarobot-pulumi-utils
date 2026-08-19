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
from datarobot_pulumi_utils.pulumi.llm_blueprint import get_blueprint_runtime_parameters

# DRUM system parameters the custom model needs in order to load at all. Submitting a
# partial runtime_parameter_values set makes the provider drop every blueprint default, so
# these must always be restated -- dropping one from the list is a load failure at deploy.
REQUIRED_DRUM_PARAMS = {
    "DEVICE_FOR_NEURAL_NETWORK_COMPUTATIONS",
    "CUSTOM_MODEL_WORKERS",
    "DRUM_SERVER_TYPE",
    "DRUM_GUNICORN_WORKER_CLASS",
    "DRUM_WORKER_CONNECTIONS",
    "DRUM_CLIENT_REQUEST_TIMEOUT",
}


def params_by_key(params):
    return {param.key: param for param in params}


def test_passes_through_the_caller_ids():
    params = params_by_key(
        get_blueprint_runtime_parameters(
            llm_blueprint_id="bp-1",
            playground_id="pg-1",
            llm_id="azure-openai-gpt-5-mini",
        )
    )

    assert params["LLM_BLUEPRINT_ID"].value == "bp-1"
    assert params["PLAYGROUND_ID"].value == "pg-1"
    assert params["LLM_ID"].value == "azure-openai-gpt-5-mini"


def test_restates_every_drum_default():
    params = params_by_key(get_blueprint_runtime_parameters("bp-1", "pg-1", "llm-1"))

    assert REQUIRED_DRUM_PARAMS <= set(params)


def test_prompt_and_blueprint_column_wiring():
    params = params_by_key(get_blueprint_runtime_parameters("bp-1", "pg-1", "llm-1"))

    assert params["PROMPT_COLUMN_NAME"].value == "promptText"
    assert params["LLM_BLUEPRINT_ID_COLUMN_NAME"].value == "LLM_BLUEPRINT_ID"
    assert params["ENABLE_LLM_BLUEPRINT_ID_COLUMN"].type == "boolean"
    assert params["ENABLE_LLM_BLUEPRINT_ID_COLUMN"].value == "true"


def test_keys_are_unique():
    params = get_blueprint_runtime_parameters("bp-1", "pg-1", "llm-1")

    keys = [param.key for param in params]
    assert len(keys) == len(set(keys))


def test_numeric_params_are_typed_numeric_with_string_values():
    # The provider expects numeric runtime parameters declared as type "numeric" but with the
    # value serialised as a string.
    params = params_by_key(get_blueprint_runtime_parameters("bp-1", "pg-1", "llm-1"))

    for key in ("CUSTOM_MODEL_WORKERS", "DRUM_WORKER_CONNECTIONS", "DRUM_CLIENT_REQUEST_TIMEOUT"):
        assert params[key].type == "numeric"
        assert isinstance(params[key].value, str)
