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


class DataRobotProjectProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        # No-op
        return CreateResult(id_=props["project_id"], outs={})

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        project_id = id
        try:
            project = dr.Project.get(project_id)
            project.delete()
            pulumi.log.info(f"Deleted DataRobot project {project_id}")
        except Exception as e:
            pulumi.log.warn(f"Failed to delete DataRobot project {project_id}: {e}")


class DataRobotProjectResource(Resource):
    def __init__(
        self,
        name: str,
        project_id: Input[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(DataRobotProjectProvider(), name, {"project_id": project_id}, opts)


class LeaderboardModelProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        # No-op
        return CreateResult(id_=f"{props['project_id']}/{props['model_id']}", outs={})

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        project_id, model_id = id.split("/", 1)
        try:
            model = dr.Model.get(project_id, model_id)
            model.delete()
            pulumi.log.info(f"Deleted DataRobot model {model_id} from project {project_id}")
        except Exception as e:
            pulumi.log.warn(f"Failed to delete DataRobot model {model_id} from project {project_id}: {e}")


class LeaderboardModelResource(Resource):
    def __init__(
        self,
        name: str,
        project_id: Input[str],
        model_id: Input[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(LeaderboardModelProvider(), name, {"project_id": project_id, "model_id": model_id}, opts)
