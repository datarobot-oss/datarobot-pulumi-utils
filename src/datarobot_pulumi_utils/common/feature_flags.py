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
import pathlib
from typing import Iterable, NamedTuple

import datarobot as dr
import pulumi
import yaml

FeatureFlagSet = dict[str, bool]


class FeatureFlagCorrection(NamedTuple):
    flag: str
    correct_value: bool


def fetch_flag_statuses(flags: Iterable[str]) -> FeatureFlagSet:
    client = dr.client.get_client()
    flags_json = {"entitlements": [{"name": flag} for flag in flags]}
    # TODO: we need to use Python SDK here (this method may be missing as of now)
    response = client.post("entitlements/evaluate/", json=flags_json)

    return {flag_status["name"]: flag_status["value"] for flag_status in response.json()["entitlements"]}


def get_corrections(desired: dict[str, bool], status: dict[str, bool]) -> list[FeatureFlagCorrection]:
    return [FeatureFlagCorrection(flag, desired[flag]) for flag in status.keys() if desired[flag] != status[flag]]


def eval_feature_flag_statuses(desired_flags: FeatureFlagSet) -> tuple[list[FeatureFlagCorrection], list[str]]:
    invalid_flags: list[str] = []

    try:
        status = fetch_flag_statuses(desired_flags.keys())

        return get_corrections(desired_flags, status), invalid_flags
    except dr.errors.ClientError as e:
        if e.status_code != 422:
            raise e

        # try to separate invalid feature flags from still valid desired flags

        for _, value in e.json["errors"].items():
            invalid_flags.append(value)

        valid_desired_flags = {k: v for k, v in desired_flags.items() if k not in invalid_flags}
        valid_desired_flag_states = fetch_flag_statuses(valid_desired_flags.keys())

        return get_corrections(valid_desired_flags, valid_desired_flag_states), invalid_flags


def check_feature_flags(yaml_path: pathlib.Path, raise_corrections: bool = True) -> None:
    """
    Find incorrect and invalid feature flags

    Returns
    -------
    A list of feature flag corrections the user needs to make and
    a list of invalid feature flags.
    """
    with open(yaml_path) as f:
        desired_flags = yaml.safe_load(f)

    desired_flags = {k: bool(v) for k, v in desired_flags.items()}

    corrections, invalid_flags = eval_feature_flag_statuses(desired_flags)

    for flag in invalid_flags:
        correct_value = desired_flags[flag]

        pulumi.warn(
            f"Feature flag '{flag}' is required to be {correct_value} but is no longer a valid DataRobot feature flag."
        )

    for flag, correct_value in corrections:
        pulumi.error(
            f"This app template requires that feature flag '{flag}' is set "
            f"to {correct_value}. Contact your DataRobot representative for "
            "assistance."
        )

    if corrections and raise_corrections:
        raise pulumi.RunError("Please correct feature flag settings and run again.")
