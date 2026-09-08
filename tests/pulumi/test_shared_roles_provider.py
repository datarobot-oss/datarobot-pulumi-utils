# Copyright 2025 DataRobot, Inc.
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

from unittest.mock import patch

import pytest

from datarobot_pulumi_utils.pulumi.shared_roles_provider import (
    DEFAULT_ROLE,
    DataRobotSharedRolesProvider,
)

MODULE = "datarobot_pulumi_utils.pulumi.shared_roles_provider"


@pytest.fixture(autouse=True)
def mock_pulumi():
    with patch(f"{MODULE}.pulumi") as m:
        yield m


@pytest.fixture(autouse=True)
def mock_dr():
    with patch(f"{MODULE}.dr") as m:
        yield m


def _search_returns(mock_dr, total, group_id="grp-1"):
    """Point the mocked client's GET at a directory search response."""
    data = [{"id": group_id}] if total else []
    mock_dr.Client.return_value.get.return_value.json.return_value = {
        "totalCount": total,
        "data": data,
    }


def _patch_calls(mock_dr):
    return mock_dr.Client.return_value.patch.call_args_list


def test_diff_no_change():
    # WHEN old and new props are equivalent
    result = DataRobotSharedRolesProvider().diff(
        "id",
        {"deployment_id": "dep-1", "group_name": "Finance", "role": "CONSUMER"},
        {"deployment_id": "dep-1", "group_name": "Finance", "role": "CONSUMER"},
    )

    # THEN there are no changes and nothing to replace
    assert result.changes is False
    assert result.replaces == []


def test_diff_deployment_id_change_forces_replace():
    # WHEN the deployment changes
    result = DataRobotSharedRolesProvider().diff(
        "id",
        {"deployment_id": "dep-1", "group_name": "Finance", "role": "CONSUMER"},
        {"deployment_id": "dep-2", "group_name": "Finance", "role": "CONSUMER"},
    )

    # THEN it is a change that requires replacing the resource
    assert result.changes is True
    assert result.replaces == ["deployment_id"]


def test_diff_group_name_change_is_update_not_replace():
    # WHEN only the group name changes
    result = DataRobotSharedRolesProvider().diff(
        "id",
        {"deployment_id": "dep-1", "group_name": "Finance", "role": "CONSUMER"},
        {"deployment_id": "dep-1", "group_name": "FinanceEMEA", "role": "CONSUMER"},
    )

    # THEN it is an in-place change, not a replacement
    assert result.changes is True
    assert result.replaces == []


def test_diff_absent_role_equals_default():
    # WHEN role is absent on one side and the default on the other
    result = DataRobotSharedRolesProvider().diff(
        "id",
        {"deployment_id": "dep-1", "group_name": "Finance"},
        {"deployment_id": "dep-1", "group_name": "Finance", "role": DEFAULT_ROLE},
    )

    # THEN that is not treated as a change
    assert result.changes is False


def test_create_grants_the_resolved_group(mock_dr):
    # GIVEN the group name resolves to exactly one group
    _search_returns(mock_dr, total=1, group_id="grp-9")

    # WHEN the share is created
    result = DataRobotSharedRolesProvider().create(
        {"deployment_id": "dep-1", "group_name": "Finance"}
    )

    # THEN the resolved id is granted the default role on that deployment
    args, kwargs = _patch_calls(mock_dr)[0]
    assert args[0] == "deployments/dep-1/sharedRoles/"
    assert kwargs["json"]["operation"] == "updateRoles"
    assert kwargs["json"]["roles"] == [
        {"shareRecipientType": "group", "id": "grp-9", "role": DEFAULT_ROLE}
    ]

    # AND the group id is recorded so it can be revoked later
    assert result.outs["group_id"] == "grp-9"
    assert result.id == "dep-1:grp-9"


def test_create_rejects_a_name_that_matches_nothing(mock_dr):
    # GIVEN no group matches the name
    _search_returns(mock_dr, total=0)

    # THEN creating the share fails rather than sharing with nobody
    with pytest.raises(ValueError, match="found 0"):
        DataRobotSharedRolesProvider().create(
            {"deployment_id": "dep-1", "group_name": "Nope"}
        )


def test_create_rejects_an_ambiguous_name(mock_dr):
    # GIVEN two groups match the name
    _search_returns(mock_dr, total=2)

    # THEN creating the share fails rather than guessing which one was meant
    with pytest.raises(ValueError, match="found 2"):
        DataRobotSharedRolesProvider().create(
            {"deployment_id": "dep-1", "group_name": "Finance"}
        )

    # AND nothing was granted
    assert _patch_calls(mock_dr) == []


def test_update_revokes_the_previous_group_first(mock_dr):
    # GIVEN the group name has changed since the last apply
    _search_returns(mock_dr, total=1, group_id="grp-new")

    # WHEN the resource is updated
    DataRobotSharedRolesProvider().update(
        "dep-1:grp-old",
        {"deployment_id": "dep-1", "group_name": "Finance", "group_id": "grp-old"},
        {"deployment_id": "dep-1", "group_name": "FinanceEMEA"},
    )

    # THEN the old grant is removed before the new one is added
    roles = [kwargs["json"]["roles"][0] for _, kwargs in _patch_calls(mock_dr)]
    assert roles[0] == {"shareRecipientType": "group", "id": "grp-old", "role": "NO_ROLE"}
    assert roles[1] == {"shareRecipientType": "group", "id": "grp-new", "role": DEFAULT_ROLE}


def test_update_does_not_revoke_when_only_the_role_changed(mock_dr):
    # GIVEN the group is unchanged and only the role differs
    _search_returns(mock_dr, total=1, group_id="grp-1")

    # WHEN the resource is updated
    DataRobotSharedRolesProvider().update(
        "dep-1:grp-1",
        {"deployment_id": "dep-1", "group_name": "Finance", "group_id": "grp-1", "role": "CONSUMER"},
        {"deployment_id": "dep-1", "group_name": "Finance", "role": "USER"},
    )

    # THEN there is no revoke, just the new role
    roles = [kwargs["json"]["roles"][0] for _, kwargs in _patch_calls(mock_dr)]
    assert roles == [{"shareRecipientType": "group", "id": "grp-1", "role": "USER"}]


def test_delete_revokes_the_recorded_group(mock_dr):
    # WHEN the share is deleted
    DataRobotSharedRolesProvider().delete(
        "dep-1:grp-1",
        {"deployment_id": "dep-1", "group_name": "Finance", "group_id": "grp-1"},
    )

    # THEN the group's access is removed
    _, kwargs = _patch_calls(mock_dr)[0]
    assert kwargs["json"]["roles"][0]["role"] == "NO_ROLE"


def test_delete_is_a_noop_without_a_recorded_group(mock_dr):
    # WHEN there is no group id in state, e.g. a failed create
    DataRobotSharedRolesProvider().delete(
        "dep-1", {"deployment_id": "dep-1", "group_name": "Finance"}
    )

    # THEN nothing is called
    assert _patch_calls(mock_dr) == []


def test_delete_does_not_fail_the_destroy(mock_dr, mock_pulumi):
    # GIVEN revoking raises, e.g. the deployment is already gone
    mock_dr.Client.return_value.patch.side_effect = RuntimeError("410 Gone")

    # WHEN the share is deleted
    DataRobotSharedRolesProvider().delete(
        "dep-1:grp-1",
        {"deployment_id": "dep-1", "group_name": "Finance", "group_id": "grp-1"},
    )

    # THEN it warns rather than failing the whole destroy
    assert mock_pulumi.log.warn.called
