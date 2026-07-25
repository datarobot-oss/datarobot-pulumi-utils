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

from datarobot_pulumi_utils.pulumi.query_dataset_provider import QueryDatasetProvider


@pytest.fixture(autouse=True)
def mock_pulumi():
    with patch("datarobot_pulumi_utils.pulumi.query_dataset_provider.pulumi") as m:
        yield m


@pytest.fixture(autouse=True)
def mock_dr():
    with patch("datarobot_pulumi_utils.pulumi.query_dataset_provider.dr") as m:
        yield m


# autospec so the create() call is validated against the real constructor
# signatures: an SDK kwarg rename/removal (e.g. across a datarobot upgrade) will
# fail the test instead of silently passing against a permissive MagicMock.
@pytest.fixture
def mock_settings():
    with patch("datarobot_pulumi_utils.pulumi.query_dataset_provider.QueryGeneratorSettings", autospec=True) as m:
        yield m


@pytest.fixture
def mock_dataset():
    with patch("datarobot_pulumi_utils.pulumi.query_dataset_provider.QueryGeneratorDataset", autospec=True) as m:
        yield m


def _create_props(**overrides):
    props = {
        "use_case_id": "uc-1",
        "dataset_id": "ds-source",
        "target": "y",
        "datetime_partition_column": "date_col",
        "time_unit": "DAY",
        "tags": ["t1"],
    }
    props.update(overrides)
    return props


def test_create_builds_settings_with_props_and_defaults(mock_dr, mock_settings, mock_dataset):
    # WHEN create runs with the minimal props (relying on defaults for the rest)
    mock_dr.DataEngineQueryGenerator.create.return_value = MagicMock(id="gen-1")
    mock_dr.Dataset.create_from_query_generator.return_value = MagicMock(id="ds-generated")

    result = QueryDatasetProvider().create(_create_props())

    # THEN the query-generator settings carry the passed values and the documented defaults
    _, settings_kwargs = mock_settings.call_args
    assert settings_kwargs["datetime_partition_column"] == "date_col"
    assert settings_kwargs["time_unit"] == "DAY"
    assert settings_kwargs["target"] == "y"
    assert settings_kwargs["time_step"] == 1
    assert settings_kwargs["default_numeric_aggregation_method"] == "sum"
    assert settings_kwargs["default_categorical_aggregation_method"] == "last"

    # AND the dataset alias defaults to "query_dataset"
    _, dataset_kwargs = mock_dataset.call_args
    assert dataset_kwargs["alias"] == "query_dataset"
    assert dataset_kwargs["dataset_id"] == "ds-source"

    # AND the generator is created with the default TimeSeries type and wired to the settings/dataset
    _, gen_kwargs = mock_dr.DataEngineQueryGenerator.create.call_args
    assert gen_kwargs["generator_type"] == "TimeSeries"
    assert gen_kwargs["generator_settings"] is mock_settings.return_value
    assert gen_kwargs["datasets"] == [mock_dataset.return_value]

    # AND the dataset is generated from the generator and returned as the resource id/outs
    mock_dr.Dataset.create_from_query_generator.assert_called_once_with(generator_id="gen-1", use_cases="uc-1")
    assert result.id == "ds-generated"
    assert result.outs["generator_id"] == "gen-1"
    assert result.outs["generated_dataset_id"] == "ds-generated"


def test_create_applies_name_and_tags(mock_dr, mock_settings, mock_dataset):
    # WHEN create runs with an explicit name and two tags
    generated = MagicMock(id="ds-generated")
    mock_dr.DataEngineQueryGenerator.create.return_value = MagicMock(id="gen-1")
    mock_dr.Dataset.create_from_query_generator.return_value = generated

    QueryDatasetProvider().create(_create_props(name="My Dataset", tags=["a", "b"]))

    # THEN the generated dataset is renamed and one tag PATCH is issued per tag
    generated.modify.assert_called_once_with(name="My Dataset")
    assert mock_dr.client.get_client.return_value.patch.call_count == 2


def test_update_recreates_on_core_property_change(mock_dr):
    # WHEN a core property (dataset_id) changes
    provider = QueryDatasetProvider()
    with patch.object(provider, "delete") as mock_delete, patch.object(provider, "create") as mock_create:
        mock_create.return_value = MagicMock(outs={"generated_dataset_id": "ds-new"})
        olds = {"dataset_id": "ds-old"}
        news = {"dataset_id": "ds-new"}

        result = provider.update("id-1", olds, news)

        # THEN the resource is destroyed and recreated, returning the new outs
        mock_delete.assert_called_once_with("id-1", olds)
        mock_create.assert_called_once_with(news)
        assert result.outs == {"generated_dataset_id": "ds-new"}


def test_update_name_and_tags_only_does_not_recreate(mock_dr):
    # WHEN only the name and tags change (all core props identical)
    provider = QueryDatasetProvider()
    dataset = MagicMock()
    mock_dr.Dataset.get.return_value = dataset
    olds = {"dataset_id": "ds", "name": "Old", "tags": ["keep"]}
    news = {"dataset_id": "ds", "name": "New", "tags": ["keep", "added"]}

    with patch.object(provider, "delete") as mock_delete, patch.object(provider, "create") as mock_create:
        result = provider.update("id-1", olds, news)

        # THEN no recreate happens
        mock_delete.assert_not_called()
        mock_create.assert_not_called()

    # AND the dataset is renamed and only the newly-added tag is applied
    dataset.modify.assert_called_once_with(name="New")
    assert mock_dr.client.get_client.return_value.patch.call_count == 1
    assert result.outs == news


def test_delete_removes_dataset_and_generator(mock_dr):
    # WHEN delete runs with a known generator id
    QueryDatasetProvider().delete("ds-1", {"generator_id": "gen-1"})

    # THEN the generated dataset is deleted and the generator is cleaned up
    mock_dr.Dataset.delete.assert_called_once_with(dataset_id="ds-1")
    mock_dr.client.get_client.return_value.delete.assert_called_once_with("dataEngineQueryGenerators/gen-1/")


def test_delete_swallows_and_warns_on_failure(mock_dr, mock_pulumi):
    # WHEN deleting the dataset raises
    mock_dr.Dataset.delete.side_effect = Exception("boom")

    # THEN the error is swallowed but surfaced as a warning (not raised)
    QueryDatasetProvider().delete("ds-1", {})

    mock_pulumi.log.warn.assert_called_once()
    assert "ds-1" in mock_pulumi.log.warn.call_args[0][0]
