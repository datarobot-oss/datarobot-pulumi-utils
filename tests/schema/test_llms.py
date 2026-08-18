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
import pytest

from datarobot_pulumi_utils.schema.llms import DEPLOYED_LLM_PLACEHOLDER_MODEL, ensure_datarobot_prefix


@pytest.mark.parametrize(
    "model_name,expected",
    [
        # Bare model name gets the prefix.
        ("gpt-5-mini", "datarobot/gpt-5-mini"),
        # provider/model gets the prefix, provider segment untouched.
        ("azure/gpt-5-mini-2025-08-07", "datarobot/azure/gpt-5-mini-2025-08-07"),
        ("bedrock/anthropic.claude-opus-4-5", "datarobot/bedrock/anthropic.claude-opus-4-5"),
        ("vertex_ai/gemini-2.5-pro", "datarobot/vertex_ai/gemini-2.5-pro"),
        # Already-prefixed values pass through unchanged (idempotent).
        ("datarobot/gpt-5-mini", "datarobot/gpt-5-mini"),
        ("datarobot/azure/gpt-5-mini", "datarobot/azure/gpt-5-mini"),
    ],
)
def test_ensure_datarobot_prefix(model_name, expected):
    assert ensure_datarobot_prefix(model_name) == expected


def test_ensure_datarobot_prefix_is_idempotent():
    once = ensure_datarobot_prefix("azure/gpt-5-mini")
    assert ensure_datarobot_prefix(once) == once


def test_ensure_datarobot_prefix_does_not_match_prefix_lookalikes():
    # A provider whose name merely starts with "datarobot" is not the unified prefix.
    assert ensure_datarobot_prefix("datarobotics/model") == "datarobot/datarobotics/model"


def test_placeholder_model_is_already_prefixed():
    # The placeholder is fed straight to ensure_datarobot_prefix by callers, so it must be a
    # fixed point -- otherwise the deployment path would send "datarobot/datarobot/...".
    assert DEPLOYED_LLM_PLACEHOLDER_MODEL.startswith("datarobot/")
    assert ensure_datarobot_prefix(DEPLOYED_LLM_PLACEHOLDER_MODEL) == DEPLOYED_LLM_PLACEHOLDER_MODEL
