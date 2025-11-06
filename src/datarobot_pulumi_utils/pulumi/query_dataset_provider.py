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

from typing import Any, Dict, List, Optional

import datarobot as dr
import pulumi
from datarobot.models.data_engine_query_generator import (
    QueryGeneratorDataset,
    QueryGeneratorSettings,
)
from pulumi import Input
from pulumi.dynamic import CreateResult, ResourceProvider, UpdateResult

client = dr.Client()


def add_dataset_tag(dataset_id: str, tag_name: str) -> None:
    """Add a tag to a dataset"""
    client.patch(
        "datasets/",
        json={"datasetIds": [dataset_id], "payload": {"action": "tag", "tags": [tag_name]}},
    )


class QueryDatasetProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        use_case_id = props["use_case_id"]
        dataset_id = props["dataset_id"]
        generator_type = props.get("generator_type", "TimeSeries")
        alias = props.get("alias", "query_dataset")
        name = props.get("name", "Query Generated Dataset")
        tags = props.get("tags", [])

        # Generator settings
        target = props.get("target")
        multiseries_id_columns = props.get("multiseries_id_columns", [])
        datetime_partition_column = props.get("datetime_partition_column")
        time_unit = props.get("time_unit")
        time_step = props.get("time_step", 1)
        default_numeric_aggregation_method = props.get("default_numeric_aggregation_method", "sum")
        default_categorical_aggregation_method = props.get("default_categorical_aggregation_method", "last")

        # Create the query generator dataset
        query_dataset = QueryGeneratorDataset(  # type: ignore[no-untyped-call]
            alias=alias,
            dataset_id=dataset_id,
        )

        # Create the generator settings
        settings = QueryGeneratorSettings(  # type: ignore[no-untyped-call]
            target=target,
            multiseries_id_columns=multiseries_id_columns,
            datetime_partition_column=datetime_partition_column,
            time_unit=time_unit,
            time_step=time_step,
            default_numeric_aggregation_method=default_numeric_aggregation_method,
            default_categorical_aggregation_method=default_categorical_aggregation_method,
        )

        # Create the query generator
        generator = dr.DataEngineQueryGenerator.create(  # type: ignore[no-untyped-call]
            generator_type=generator_type,
            datasets=[query_dataset],
            generator_settings=settings,
        )

        # Create dataset from the query generator
        generated_dataset: dr.Dataset = dr.Dataset.create_from_query_generator(
            generator_id=generator.id, use_cases=use_case_id
        )

        # Update dataset name
        if name:
            generated_dataset.modify(name=name)

        # Add tags
        for tag in tags:
            add_dataset_tag(generated_dataset.id, tag)

        outputs = {
            **props,
            "generator_id": generator.id,
            "generated_dataset_id": generated_dataset.id,
        }
        return CreateResult(id_=generated_dataset.id, outs=outputs)

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        try:
            # Delete the generated dataset
            dr.Dataset.delete(dataset_id=id)

            # Delete the generator if it exists
            generator_id = props.get("generator_id")
            if generator_id:
                try:
                    client.delete(f"dataEngineQueryGenerators/{generator_id}/")
                except Exception:
                    # Generator might already be deleted or not exist
                    pass
        except Exception:
            # Dataset might already be deleted
            pass

    def update(self, id: str, olds: Dict[str, Any], news: Dict[str, Any]) -> UpdateResult:
        # Check if core properties changed that require recreation
        core_props = [
            "use_case_id",
            "dataset_id",
            "generator_type",
            "target",
            "multiseries_id_columns",
            "datetime_partition_column",
            "time_unit",
            "time_step",
            "default_numeric_aggregation_method",
            "default_categorical_aggregation_method",
            "alias",
        ]

        if any(olds.get(prop) != news.get(prop) for prop in core_props):
            # Core properties changed, need to recreate
            self.delete(id, olds)
            create_result = self.create(news)
            return UpdateResult(outs=create_result.outs)

        # Handle name change
        if olds.get("name") != news.get("name"):
            dataset = dr.Dataset.get(id)
            name = news.get("name", "Query Generated Dataset")
            dataset.modify(name=name)

        # Handle tag changes
        old_tags = set(olds.get("tags", []))
        new_tags = set(news.get("tags", []))

        # Add new tags
        for tag in new_tags - old_tags:
            add_dataset_tag(id, tag)

        return UpdateResult(outs=news)


class QueryDatasetResource(pulumi.dynamic.Resource):
    def __init__(
        self,
        name: str,
        use_case_id: Input[str],
        dataset_id: Input[str],
        generator_type: Optional[Input[str]] = None,
        alias: Optional[Input[str]] = None,
        target: Optional[Input[str]] = None,
        multiseries_id_columns: Optional[Input[List[str]]] = None,
        datetime_partition_column: Optional[Input[str]] = None,
        time_unit: Optional[Input[str]] = None,
        time_step: Optional[Input[int]] = None,
        default_numeric_aggregation_method: Optional[Input[str]] = None,
        default_categorical_aggregation_method: Optional[Input[str]] = None,
        tags: Optional[Input[List[str]]] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        props = {
            "use_case_id": use_case_id,
            "dataset_id": dataset_id,
            "generator_type": generator_type,
            "alias": alias,
            "name": name,
            "target": target,
            "multiseries_id_columns": multiseries_id_columns,
            "datetime_partition_column": datetime_partition_column,
            "time_unit": time_unit,
            "time_step": time_step,
            "default_numeric_aggregation_method": default_numeric_aggregation_method,
            "default_categorical_aggregation_method": default_categorical_aggregation_method,
            "tags": tags,
        }
        super().__init__(QueryDatasetProvider(), name, props, opts)
