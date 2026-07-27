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
from unittest.mock import patch

import pytest

from datarobot_pulumi_utils.pulumi.dataset_provider import DataRobotDatasetProvider


@pytest.fixture(autouse=True)
def mock_pulumi():
    with patch("datarobot_pulumi_utils.pulumi.dataset_provider.pulumi") as m:
        yield m


@pytest.fixture(autouse=True)
def mock_dr():
    with patch("datarobot_pulumi_utils.pulumi.dataset_provider.dr") as m:
        yield m


def test_diff_no_change():
    # WHEN old and new props are equivalent
    result = DataRobotDatasetProvider().diff(
        "id", {"dataset_id": "ds-1", "managed": True}, {"dataset_id": "ds-1", "managed": True}
    )

    # THEN there are no changes and nothing to replace
    assert result.changes is False
    assert result.replaces == []


def test_diff_dataset_id_change_forces_replace():
    # WHEN the dataset_id changes
    result = DataRobotDatasetProvider().diff(
        "id", {"dataset_id": "ds-1", "managed": True}, {"dataset_id": "ds-2", "managed": True}
    )

    # THEN it is a change that requires replacing the resource
    assert result.changes is True
    assert result.replaces == ["dataset_id"]


def test_diff_managed_only_change_is_update_not_replace():
    # WHEN only `managed` changes
    result = DataRobotDatasetProvider().diff(
        "id", {"dataset_id": "ds-1", "managed": False}, {"dataset_id": "ds-1", "managed": True}
    )

    # THEN it is an in-place change, not a replacement
    assert result.changes is True
    assert result.replaces == []


def test_diff_managed_none_equals_false():
    # WHEN managed is None on one side and False (or absent) on the other
    result = DataRobotDatasetProvider().diff(
        "id", {"dataset_id": "ds-1", "managed": None}, {"dataset_id": "ds-1"}
    )

    # THEN normalization treats both as False, so there is no diff
    assert result.changes is False
    assert result.replaces == []


def test_delete_skips_unmanaged_dataset(mock_dr):
    # WHEN deleting an unmanaged dataset
    DataRobotDatasetProvider().delete("ds-1", {"dataset_id": "ds-1", "managed": False})

    # THEN the dataset is NOT deleted from DataRobot (data-safety guard)
    mock_dr.Dataset.delete.assert_not_called()


def test_delete_removes_managed_dataset(mock_dr):
    # WHEN deleting a managed dataset
    DataRobotDatasetProvider().delete("ds-1", {"dataset_id": "ds-1", "managed": True})

    # THEN the dataset is deleted from DataRobot
    mock_dr.Dataset.delete.assert_called_once_with("ds-1")


def test_delete_managed_swallows_and_warns_on_failure(mock_dr, mock_pulumi):
    # WHEN deleting a managed dataset raises
    mock_dr.Dataset.delete.side_effect = Exception("boom")

    # THEN the failure is swallowed but surfaced as a warning (not raised)
    DataRobotDatasetProvider().delete("ds-1", {"dataset_id": "ds-1", "managed": True})

    mock_pulumi.log.warn.assert_called_once()
    assert "ds-1" in mock_pulumi.log.warn.call_args[0][0]
