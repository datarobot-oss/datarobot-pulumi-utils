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
import os
import re
from typing import Optional

import datarobot as dr
import pulumi
from datarobot.enums import EXECUTION_ENVIRONMENT_VERSION_BUILD_STATUS


def resolve_execution_environment_version(
    execution_environment_id: str,
    version_env_var: str,
) -> Optional[str]:
    """Resolve execution environment version ID from environment variable; None means use latest.

    Reads and validates the pinned version from the given env var.
    If the version is not found (e.g. on-prem environment lacks it), logs a warning
    and returns None so the caller uses latest.
    """
    requested_version_id = os.environ.get(version_env_var, None)
    if requested_version_id:
        requested_version_id = requested_version_id.strip("'\"")
    if not re.match(r"^[a-f0-9]{24}$", str(requested_version_id or "")):
        pulumi.info("No valid execution environment version ID provided, using latest version.")
        return None
    try:
        version = dr.ExecutionEnvironmentVersion.get(execution_environment_id, str(requested_version_id))
        if version.build_status == EXECUTION_ENVIRONMENT_VERSION_BUILD_STATUS.SUCCESS:
            return version.id
        pulumi.warn(
            f"⚠️ Requested execution environment version {requested_version_id} "
            f"is not successfully built for environment {execution_environment_id} "
            f"(build_status: {version.build_status}); using latest."
        )
        return None
    except dr.errors.ClientError:
        pulumi.warn(
            f"⚠️ Requested execution environment version {requested_version_id} "
            f"not found for environment {execution_environment_id}; using latest."
        )
    return None
