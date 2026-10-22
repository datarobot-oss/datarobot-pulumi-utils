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
from enum import Enum

import datarobot as dr

from datarobot_pulumi_utils.schema.base import Schema


class RuntimeEnvironment(Schema):
    name: str
    # Names tried in order when `name` is not found, e.g. when an environment is renamed
    # and the DataRobot instance may carry either the old or the new name.
    fallback_names: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        client = dr.client.get_client()
        names = (self.name, *self.fallback_names)
        try:
            # TODO: Consider using Python SDK here instead of bare requests:
            #  https://datarobot-public-api-client.readthedocs-hosted.com/en/latest-release/custom_models.html#datarobot.ExecutionEnvironment.list
            for name in names:
                environments = client.get("executionEnvironments/", params={"searchFor": name}).json()
                env_id: str | None = next(
                    (environment["id"] for environment in environments["data"] if environment["name"] == name),
                    None,
                )
                if env_id is not None:
                    return env_id
        except Exception as e:
            raise ValueError(f"Could not find the Execution Environment ID for {self.name}") from e
        raise ValueError(f"Could not find the Execution Environment ID for any of: {', '.join(names)}")


class RuntimeEnvironments(Enum):
    PYTHON_312_APPLICATION_BASE = RuntimeEnvironment(
        name="[DataRobot] Python 3.12 Applications Base",
    )
    PYTHON_311_NOTEBOOK_BASE = RuntimeEnvironment(
        name="[DataRobot] Python 3.11 Notebook Base Image",
    )
    PYTHON_311_MODERATIONS = RuntimeEnvironment(name="[GenAI] Python 3.11 with Moderations")
    # The GenAI moderations environment was upgraded from Python 3.12 to 3.14 and renamed in place
    # (same environment ID), so each name falls back to the other to work across DataRobot versions.
    PYTHON_312_MODERATIONS = RuntimeEnvironment(
        name="[GenAI] Python 3.12 with Moderations",
        fallback_names=("[GenAI] Python 3.14 with Moderations",),
    )
    PYTHON_314_MODERATIONS = RuntimeEnvironment(
        name="[GenAI] Python 3.14 with Moderations",
        fallback_names=("[GenAI] Python 3.12 with Moderations",),
    )
    PYTHON_39_CUSTOM_METRICS = RuntimeEnvironment(name="[DataRobot] Python 3.9 Custom Metrics Templates Drop-In")
    PYTHON_311_NOTEBOOK_DROP_IN = RuntimeEnvironment(name="[DataRobot] Python 3.11 Notebook Drop-In")
    PYTHON_39_STREAMLIT = RuntimeEnvironment(name="[Experimental] Python 3.9 Streamlit")
    PYTHON_3_GENAI_AGENTS = RuntimeEnvironment(name="[DataRobot] Python 3 GenAI Agents")
    PYTHON_311_GENAI_AGENTS = RuntimeEnvironment(name="[DataRobot] Python 3.11 GenAI Agents")
    PYTHON_311_GENAI = RuntimeEnvironment(name="[DataRobot] Python 3.11 GenAI")
    PYTHON_39_GENAI = RuntimeEnvironment(name="[DataRobot] Python 3.9 GenAI")
    PYTHON_3_MCP = RuntimeEnvironment(name="[DataRobot] Python 3 MCP")
    PYTHON_39_ONNX = RuntimeEnvironment(name="[DataRobot] Python 3.9 ONNX Drop-In")
    JULIA_DROP_IN = RuntimeEnvironment(name="[DataRobot] Julia Drop-In")
    PYTHON_39_PMML = RuntimeEnvironment(name="[DataRobot] Python 3.9 PMML Drop-In")
    R_421_DROP_IN = RuntimeEnvironment(name="[DataRobot] R 4.2.1 Drop-In")
    PYTHON_39_PYTORCH = RuntimeEnvironment(name="[DataRobot] Python 3.9 PyTorch Drop-In")
    JAVA_11_DROP_IN = RuntimeEnvironment(name="[DataRobot] Java 11 Drop-In (DR Codegen, H2O)")
    PYTHON_39_SCIKIT_LEARN = RuntimeEnvironment(name="[DataRobot] Python 3.9 Scikit-Learn Drop-In")
    PYTHON_39_XGBOOST = RuntimeEnvironment(name="[DataRobot] Python 3.9 XGBoost Drop-In")
    PYTHON_39_KERAS = RuntimeEnvironment(name="[DataRobot] Python 3.9 Keras Drop-In")
