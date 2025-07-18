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

import pulumi
from datarobot.models.deployment.challenger import Challenger
from pulumi import Input
from pulumi.dynamic import CreateResult, Resource, ResourceProvider


class ChallengerProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        deployment_id = props["deployment_id"]
        model_package_id = props["model_package_id"]
        prediction_environment_id = props["prediction_environment_id"]
        try:
            challenger = Challenger.create(
                name=props.get("name", f"Challenger-{model_package_id}"),
                deployment_id=deployment_id,
                model_package_id=model_package_id,
                prediction_environment_id=prediction_environment_id,
            )
            return CreateResult(
                id_=challenger.id,
                outs={
                    "challenger_id": challenger.id,
                    "deployment_id": deployment_id,
                    "model_package_id": model_package_id,
                    "prediction_environment_id": prediction_environment_id,
                },
            )
        except Exception as e:
            pulumi.log.error(f"Failed to create DataRobot challenger: {e}")
            raise e

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        try:
            challenger = Challenger.get(deployment_id=props["deployment_id"], challenger_id=id)
            challenger.delete()
        except Exception as e:
            pulumi.log.warn(f"Failed to delete DataRobot challenger {id}: {e}")


class ChallengerResource(Resource):
    def __init__(
        self,
        name: str,
        deployment_id: Input[str],
        model_package_id: Input[str],
        prediction_environment_id: Input[str],
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(
            ChallengerProvider(),
            name,
            {
                "deployment_id": deployment_id,
                "model_package_id": model_package_id,
                "prediction_environment_id": prediction_environment_id,
            },
            opts,
        )
