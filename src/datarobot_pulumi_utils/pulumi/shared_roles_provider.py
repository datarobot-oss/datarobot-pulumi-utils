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

DEFAULT_ROLE = "CONSUMER"
"""Read-only tier for a deployment. Consumers can make predictions but cannot view it."""

NO_ROLE = "NO_ROLE"
"""Sentinel the sharing API converts to ``None``, which removes access."""


def _resolve_group_id(group_name: str) -> str:
    """Resolve a directory group name to its DataRobot group ID.

    Matching is exact and case-sensitive, so ``group_name`` must be spelled exactly
    as it appears in the identity provider. The endpoint returns every match with a
    count rather than erroring, so an ambiguous name is rejected here.
    """
    client = dr.Client()
    response = client.get(
        "directoryEntities/",
        params={"entityType": "group", "name": group_name},
    )
    body = response.json()
    total = body["totalCount"]
    if total != 1:
        raise ValueError(
            f"Expected exactly one group named {group_name!r}, found {total}. "
            "Group names are matched exactly and case-sensitively."
        )
    group_id: str = body["data"][0]["id"]
    return group_id


def _set_role(deployment_id: str, group_id: str, role: str) -> None:
    """Grant ``role`` on a deployment to a group, or remove it with ``NO_ROLE``.

    ``updateRoles`` has set semantics rather than append, so re-applying an
    unchanged role is a no-op.
    """
    client = dr.Client()
    client.patch(
        f"deployments/{deployment_id}/sharedRoles/",
        json={
            "operation": "updateRoles",
            "roles": [
                {
                    "shareRecipientType": "group",
                    "id": group_id,
                    "role": role,
                }
            ],
        },
    )


class DataRobotSharedRolesProvider(ResourceProvider):
    """Shares a DataRobot deployment with a directory group, by group name."""

    def _normalize_props(self, props: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize properties to handle default values consistently."""
        return {
            "deployment_id": props.get("deployment_id"),
            "group_name": props.get("group_name"),
            "role": props.get("role") or DEFAULT_ROLE,
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
                if key == "deployment_id":
                    replaces.append(key)

        return DiffResult(changes=changes, replaces=replaces)

    def create(self, props: Dict[str, Any]) -> CreateResult:
        normalized_props = self._normalize_props(props)
        deployment_id = normalized_props["deployment_id"]
        group_name = normalized_props["group_name"]
        role = normalized_props["role"]

        group_id = _resolve_group_id(group_name)
        _set_role(deployment_id, group_id, role)

        return CreateResult(
            id_=f"{deployment_id}:{group_id}",
            outs={
                "deployment_id": deployment_id,
                "group_name": group_name,
                "role": role,
                "group_id": group_id,
            },
        )

    def update(self, id: str, _olds: Dict[str, Any], _news: Dict[str, Any]) -> UpdateResult:
        normalized_olds = self._normalize_props(_olds)
        normalized_news = self._normalize_props(_news)

        deployment_id = normalized_news["deployment_id"]
        group_name = normalized_news["group_name"]
        role = normalized_news["role"]

        previous_group_id = _olds.get("group_id")
        if previous_group_id and normalized_olds["group_name"] != group_name:
            # The grant is keyed on the group, so revoke the old one before adding
            # the new. Without this a renamed variable would leave a stale grant.
            _set_role(deployment_id, previous_group_id, NO_ROLE)

        group_id = _resolve_group_id(group_name)
        _set_role(deployment_id, group_id, role)

        return UpdateResult(
            outs={
                "deployment_id": deployment_id,
                "group_name": group_name,
                "role": role,
                "group_id": group_id,
            }
        )

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        normalized_props = self._normalize_props(props)
        deployment_id = normalized_props["deployment_id"]
        group_id = props.get("group_id")

        if not group_id:
            pulumi.log.info(f"No group id recorded for share {id}, nothing to revoke")
            return
        try:
            pulumi.log.info(f"Revoking group {group_id} access on deployment {deployment_id}")
            _set_role(deployment_id, group_id, NO_ROLE)
        except Exception as e:
            pulumi.log.warn(f"Failed to revoke group {group_id} on deployment {deployment_id}: {e}")


class DataRobotSharedRolesResource(Resource):
    group_id: pulumi.Output[str]

    def __init__(
        self,
        name: str,
        deployment_id: Input[str],
        group_name: Input[str],
        role: Optional[Input[str]] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        props = {
            "deployment_id": deployment_id,
            "group_name": group_name,
            "role": role or DEFAULT_ROLE,
            "group_id": None,
        }
        super().__init__(DataRobotSharedRolesProvider(), name, props, opts)
