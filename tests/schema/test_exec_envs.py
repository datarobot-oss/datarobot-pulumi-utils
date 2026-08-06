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

from datarobot_pulumi_utils.schema.exec_envs import RuntimeEnvironment, RuntimeEnvironments


@pytest.fixture
def mock_client():
    """Serve executionEnvironments/ out of a caller-supplied {name: id} catalog."""
    with patch("datarobot_pulumi_utils.schema.exec_envs.dr") as mock_dr:
        client = MagicMock()
        mock_dr.client.get_client.return_value = client

        def catalog(available):
            def get(_url, params):
                search_for = params["searchFor"]
                response = MagicMock()
                response.json.return_value = {
                    "data": [{"id": env_id, "name": name} for name, env_id in available.items() if name == search_for]
                }
                return response

            client.get.side_effect = get
            return client

        yield catalog


def test_resolves_primary_name(mock_client):
    client = mock_client({"[DataRobot] Python 3 GenAI Agents": "new-id"})
    env = RuntimeEnvironment(name="[DataRobot] Python 3 GenAI Agents", fallback_names=["[DataRobot] Old Name"])

    assert env.id == "new-id"
    # THEN the fallback is never queried, since the primary name hit
    assert client.get.call_count == 1


def test_falls_back_when_primary_name_is_absent(mock_client):
    client = mock_client({"[DataRobot] Old Name": "old-id"})
    env = RuntimeEnvironment(name="[DataRobot] Python 3 GenAI Agents", fallback_names=["[DataRobot] Old Name"])

    assert env.id == "old-id"
    assert client.get.call_count == 2


def test_raises_when_no_name_matches(mock_client):
    mock_client({"[DataRobot] Something Else": "other-id"})
    env = RuntimeEnvironment(name="[DataRobot] Python 3 GenAI Agents", fallback_names=["[DataRobot] Old Name"])

    with pytest.raises(ValueError) as exc_info:
        _ = env.id

    # THEN the message names every candidate that was tried, not just the primary
    assert "[DataRobot] Python 3 GenAI Agents" in str(exc_info.value)
    assert "[DataRobot] Old Name" in str(exc_info.value)


def test_environment_without_fallbacks_queries_only_its_own_name(mock_client):
    client = mock_client({})
    env = RuntimeEnvironment(name="[DataRobot] Python 3.9 GenAI")

    with pytest.raises(ValueError):
        _ = env.id
    assert client.get.call_count == 1


@pytest.mark.parametrize(
    "member,expected_id",
    [
        (RuntimeEnvironments.PYTHON_3_GENAI_AGENTS, "agents-id"),
        (RuntimeEnvironments.PYTHON_311_GENAI_AGENTS, "agents-id"),
    ],
)
@pytest.mark.parametrize(
    "published_name",
    ["[DataRobot] Python 3 GenAI Agents", "[DataRobot] Python 3.11 GenAI Agents"],
)
def test_genai_agents_constants_resolve_under_either_published_name(mock_client, member, expected_id, published_name):
    """Both constants must keep working while the rename rolls out to production."""
    mock_client({published_name: expected_id})

    assert member.value.id == expected_id
