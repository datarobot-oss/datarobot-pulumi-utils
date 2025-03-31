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

from pathlib import Path
from unittest import mock

import pulumi
import pytest

from datarobot_pulumi_utils.common import check_feature_flags

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test__check_feature_flags__valid_flags():
    reqs_path = FIXTURES_DIR / "reqs.yaml"

    with mock.patch("datarobot_pulumi_utils.common.feature_flags.fetch_flag_statuses") as feature_flag_status_mock:
        feature_flag_status_mock.return_value = {
            "ENABLE_MLOPS": True,
            "ENABLE_CUSTOM_INFERENCE_MODEL": True,
            "ENABLE_PUBLIC_NETWORK_ACCESS_FOR_ALL_CUSTOM_MODELS": True,
            "ENABLE_MLOPS_TEXT_GENERATION_TARGET_TYPE": True,
        }

        check_feature_flags(reqs_path, raise_corrections=True)

def test__check_feature_flags__invalid_flag_state():
    reqs_path = FIXTURES_DIR / "reqs.yaml"

    with mock.patch("datarobot_pulumi_utils.common.feature_flags.fetch_flag_statuses") as feature_flag_status_mock:
        feature_flag_status_mock.return_value = {
            "ENABLE_MLOPS": True,
            "ENABLE_CUSTOM_INFERENCE_MODEL": True,
            "ENABLE_PUBLIC_NETWORK_ACCESS_FOR_ALL_CUSTOM_MODELS": True,
            "ENABLE_MLOPS_TEXT_GENERATION_TARGET_TYPE": False,
        }

        with pytest.raises(pulumi.RunError):
            check_feature_flags(reqs_path, raise_corrections=True)