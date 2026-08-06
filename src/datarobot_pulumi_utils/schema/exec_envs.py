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

from datarobot_pulumi_utils.schema.base import Field, Schema


class RuntimeEnvironment(Schema):
    name: str
    # Other names this same environment is or was published under. The platform keeps one
    # environment per id, so renaming it in place changes the only string the lookup below can
    # match on. Without a fallback, a rename breaks every already-deployed project that resolves
    # the environment by its old constant. Tried in order, after `name`.
    fallback_names: list[str] = Field(default_factory=list)

    @property
    def id(self) -> str:
        client = dr.client.get_client()
        failures = []
        for candidate in (self.name, *self.fallback_names):
            try:
                # TODO: Consider using Python SDK here instead of bare requests:
                #  https://datarobot-public-api-client.readthedocs-hosted.com/en/latest-release/custom_models.html#datarobot.ExecutionEnvironment.list
                environments = client.get("executionEnvironments/", params={"searchFor": candidate}).json()
                env_id: str = next(
                    environment["id"] for environment in environments["data"] if environment["name"] == candidate
                )
                return env_id
            except Exception as e:
                failures.append(f"{candidate!r} ({e})")
        raise ValueError(f"Could not find the Execution Environment ID for {self.name}. Tried: {', '.join(failures)}")


class RuntimeEnvironments(Enum):
    PYTHON_312_APPLICATION_BASE = RuntimeEnvironment(
        name="[DataRobot] Python 3.12 Applications Base",
    )
    PYTHON_311_NOTEBOOK_BASE = RuntimeEnvironment(
        name="[DataRobot] Python 3.11 Notebook Base Image",
    )
    PYTHON_311_MODERATIONS = RuntimeEnvironment(name="[GenAI] Python 3.11 with Moderations")
    PYTHON_312_MODERATIONS = RuntimeEnvironment(name="[GenAI] Python 3.12 with Moderations")
    PYTHON_39_CUSTOM_METRICS = RuntimeEnvironment(name="[DataRobot] Python 3.9 Custom Metrics Templates Drop-In")
    PYTHON_311_NOTEBOOK_DROP_IN = RuntimeEnvironment(name="[DataRobot] Python 3.11 Notebook Drop-In")
    PYTHON_39_STREAMLIT = RuntimeEnvironment(name="[Experimental] Python 3.9 Streamlit")
    # The GenAI Agents environment dropped its Python minor version from its name when it moved
    # to Python 3.13, so that future interpreter bumps no longer require a rename. The two
    # constants point at the same environment and fall back to each other, which keeps existing
    # deployments resolving while the new name rolls out to production.
    PYTHON_3_GENAI_AGENTS = RuntimeEnvironment(
        name="[DataRobot] Python 3 GenAI Agents",
        fallback_names=["[DataRobot] Python 3.11 GenAI Agents"],
    )
    PYTHON_311_GENAI_AGENTS = RuntimeEnvironment(
        name="[DataRobot] Python 3.11 GenAI Agents",
        fallback_names=["[DataRobot] Python 3 GenAI Agents"],
    )
    PYTHON_311_GENAI = RuntimeEnvironment(name="[DataRobot] Python 3.11 GenAI")
    PYTHON_39_GENAI = RuntimeEnvironment(name="[DataRobot] Python 3.9 GenAI")
    PYTHON_39_ONNX = RuntimeEnvironment(name="[DataRobot] Python 3.9 ONNX Drop-In")
    JULIA_DROP_IN = RuntimeEnvironment(name="[DataRobot] Julia Drop-In")
    PYTHON_39_PMML = RuntimeEnvironment(name="[DataRobot] Python 3.9 PMML Drop-In")
    R_421_DROP_IN = RuntimeEnvironment(name="[DataRobot] R 4.2.1 Drop-In")
    PYTHON_39_PYTORCH = RuntimeEnvironment(name="[DataRobot] Python 3.9 PyTorch Drop-In")
    JAVA_11_DROP_IN = RuntimeEnvironment(name="[DataRobot] Java 11 Drop-In (DR Codegen, H2O)")
    PYTHON_39_SCIKIT_LEARN = RuntimeEnvironment(name="[DataRobot] Python 3.9 Scikit-Learn Drop-In")
    PYTHON_39_XGBOOST = RuntimeEnvironment(name="[DataRobot] Python 3.9 XGBoost Drop-In")
    PYTHON_39_KERAS = RuntimeEnvironment(name="[DataRobot] Python 3.9 Keras Drop-In")
