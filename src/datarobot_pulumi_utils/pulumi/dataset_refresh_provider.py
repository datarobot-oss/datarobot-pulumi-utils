# Copyright 2024 DataRobot, Inc.
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

import json
from typing import Any, Dict, Optional, Union

import datarobot as dr
import pulumi
from pulumi import Input
from pulumi.dynamic import CreateResult, ResourceProvider, UpdateResult

client = dr.Client()


def schedule_dataset_refresh(
    dataset_id: str, credential_id: str, name: str, schedule: Union[Dict[str, Any], str]
) -> str:
    """Schedule a dataset refresh job"""
    if isinstance(schedule, str):
        schedule = json.loads(schedule)

    resp = client.post(
        f"datasets/{dataset_id}/refreshJobs/",
        {
            "credentialId": credential_id,
            "enabled": True,
            "name": name,
            "schedule": schedule,
        },
    )
    data = resp.json()
    return str(data["jobId"])


class RefreshPolicyProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        dataset_id = props["dataset_id"]
        credential_id = props["credential_id"]
        name = props.get("name", "Data Refresh Job")
        schedule = props.get("schedule", "{}")
        refresh_id = schedule_dataset_refresh(dataset_id, credential_id, name, schedule)

        outputs = {**props, "dataset_id": dataset_id, "refresh_id": refresh_id}
        return CreateResult(id_=f"{dataset_id}:{refresh_id}", outs=outputs)

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        dataset_id, refresh_id = id.split(":")
        client.delete(f"datasets/{dataset_id}/refreshJobs/{refresh_id}")

    def update(self, id: str, olds: Dict[str, Any], news: Dict[str, Any]) -> UpdateResult:
        self.delete(id, olds)
        create_result = self.create(news)
        return UpdateResult(outs=create_result.outs)


class RefreshPolicyResource(pulumi.dynamic.Resource):
    def __init__(
        self,
        name: str,
        dataset_id: Input[str],
        credential_id: Input[str],
        schedule: Optional[Union[Dict[str, Any], str]] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        props = {
            "dataset_id": dataset_id,
            "credential_id": credential_id,
            "name": name,
            "schedule": schedule,
        }
        super().__init__(RefreshPolicyProvider(), name, props, opts)
