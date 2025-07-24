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

from typing import Any, Dict, Optional

import datarobot as dr
import pulumi
from pulumi import Input
from pulumi.dynamic import CreateResult, DiffResult, Resource, ResourceProvider, UpdateResult


class DataRobotDatasetProvider(ResourceProvider):
    def _normalize_props(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize properties to handle default values consistently."""
        return {
            "dataset_id": props.get("dataset_id"),
            "managed": props.get("managed", False) if props.get("managed") is not None else False,
        }

    def diff(self, _id: str, _olds: Dict[str, Any], _news: Dict[str, Any]) -> DiffResult:
        normalized_olds = self._normalize_props(_olds)
        normalized_news = self._normalize_props(_news)

        changes = False
        replaces: list[str] = []

        for key, new_value in normalized_news.items():
            old_value = normalized_olds.get(key)
            if old_value != new_value:
                changes = True
                if key == "dataset_id" and old_value != new_value:
                    replaces.append(key)

        return DiffResult(changes=changes, replaces=replaces)

    def create(self, props: Dict[str, Any]) -> CreateResult:
        normalized_props = self._normalize_props(props)
        return CreateResult(
            id_=normalized_props["dataset_id"],
            outs={"dataset_id": normalized_props["dataset_id"], "managed": normalized_props["managed"]},
        )

    def update(self, id: str, _olds: Dict[str, Any], _news: Dict[str, Any]) -> UpdateResult:
        normalized_news = self._normalize_props(_news)
        return UpdateResult(outs={"dataset_id": normalized_news["dataset_id"], "managed": normalized_news["managed"]})

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        normalized_props = self._normalize_props(props)
        managed = normalized_props.get("managed", False)

        if not managed:
            pulumi.log.info(f"Skipping deletion of unmanaged dataset with ID: {id}")
            return
        try:
            pulumi.log.info(f"Attempting to delete managed dataset with ID: {id}")
            dr.Dataset.delete(id)
        except Exception:
            pass


class DataRobotDatasetResource(Resource):
    dataset_id: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        dataset_id: Input[str],
        managed: Optional[bool] = False,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        props = {
            "dataset_id": dataset_id,
            "managed": managed,
        }
        super().__init__(DataRobotDatasetProvider(), name, props, opts)
