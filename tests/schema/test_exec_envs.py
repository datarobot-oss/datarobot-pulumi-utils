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
def client():
    """A DataRobot client whose executionEnvironments search returns environments by exact name."""
    environments: dict[str, str] = {}

    def get(url, params):
        search = params["searchFor"]
        response = MagicMock()
        response.json.return_value = {
            "data": [{"id": env_id, "name": name} for name, env_id in environments.items() if search in name]
        }
        return response

    mock_client = MagicMock()
    mock_client.get.side_effect = get
    mock_client.environments = environments
    with patch("datarobot_pulumi_utils.schema.exec_envs.dr.client.get_client", return_value=mock_client):
        yield mock_client


def test_id_resolves_primary_name(client):
    client.environments["Env A"] = "id-a"
    client.environments["Env A (legacy)"] = "id-legacy"

    assert RuntimeEnvironment(name="Env A").id == "id-a"


def test_id_falls_back_to_next_name(client):
    client.environments["Env Old"] = "id-old"

    env = RuntimeEnvironment(name="Env New", fallback_names=("Env Missing", "Env Old"))

    assert env.id == "id-old"
    assert [c.kwargs["params"]["searchFor"] for c in client.get.call_args_list] == [
        "Env New",
        "Env Missing",
        "Env Old",
    ]


def test_id_prefers_primary_name_over_fallback(client):
    client.environments["Env New"] = "id-new"
    client.environments["Env Old"] = "id-old"

    env = RuntimeEnvironment(name="Env New", fallback_names=("Env Old",))

    assert env.id == "id-new"
    assert client.get.call_count == 1


def test_id_raises_when_no_name_matches(client):
    env = RuntimeEnvironment(name="Env New", fallback_names=("Env Old",))

    with pytest.raises(ValueError, match="Env New, Env Old"):
        _ = env.id


def test_id_wraps_client_errors(client):
    client.get.side_effect = RuntimeError("boom")

    with pytest.raises(ValueError, match="Env New"):
        _ = RuntimeEnvironment(name="Env New").id


@pytest.mark.parametrize(
    "available_name",
    ["[GenAI] Python 3.12 with Moderations", "[GenAI] Python 3.14 with Moderations"],
)
@pytest.mark.parametrize(
    "member",
    [RuntimeEnvironments.PYTHON_312_MODERATIONS, RuntimeEnvironments.PYTHON_314_MODERATIONS],
)
def test_moderations_resolves_under_either_name(client, member, available_name):
    client.environments[available_name] = "moderations-id"

    assert member.value.id == "moderations-id"
