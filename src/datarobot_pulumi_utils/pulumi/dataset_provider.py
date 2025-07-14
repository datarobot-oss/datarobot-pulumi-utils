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
from pulumi.dynamic import CreateResult, Resource, ResourceProvider


class DataRobotDatasetProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        # No-op
        return CreateResult(id_=props["dataset_id"], outs={})

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        try:
            pulumi.log.info(f"Attempting to delete dataset with ID: {id}")
            dr.Dataset.delete(id)
        except Exception:
            pass


class DataRobotDatasetResource(Resource):
    def __init__(
        self,
        name: str,
        dataset_id: Input[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(DataRobotDatasetProvider(), name, {"dataset_id": dataset_id}, opts)
