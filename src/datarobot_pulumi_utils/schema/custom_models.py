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
from __future__ import annotations

from enum import Enum

import pulumi_datarobot as drp

from datarobot_pulumi_utils.schema.base import Schema, StrEnum
from datarobot_pulumi_utils.schema.common import ResourceBundle


class CustomModelResourceBundles(Enum):
    CPU_XXS = ResourceBundle(name="XXS", description="1 CPU | 128MB RAM", id="cpu.nano")
    CPU_XS = ResourceBundle(name="XS", description="1 CPU | 256MB RAM", id="cpu.micro")
    CPU_S = ResourceBundle(name="S", description="1 CPU | 512MB RAM", id="cpu.small")
    CPU_M = ResourceBundle(name="M", description="1 CPU | 1GB RAM", id="cpu.medium")
    CPU_L = ResourceBundle(name="L", description="2 CPU | 1.5GB RAM", id="cpu.large")
    CPU_XL = ResourceBundle(name="XL", description="2 CPU | 2GB RAM", id="cpu.xlarge")
    CPU_XXL = ResourceBundle(name="XXL", description="2 CPU | 3GB RAM", id="cpu.2xlarge")
    CPU_3XL = ResourceBundle(name="3XL", description="2 CPU | 4GB RAM", id="cpu.3xlarge")
    CPU_4XL = ResourceBundle(name="4XL", description="2 CPU | 6GB RAM", id="cpu.4xlarge")
    CPU_5XL = ResourceBundle(name="5XL", description="2 CPU | 8GB RAM", id="cpu.5xlarge")
    CPU_6XL = ResourceBundle(name="6XL", description="2 CPU | 10GB RAM", id="cpu.6xlarge")
    CPU_7XL = ResourceBundle(name="7XL", description="2 CPU | 12GB RAM", id="cpu.7xlarge")
    CPU_8XL = ResourceBundle(name="8XL", description="2 CPU | 14GB RAM", id="cpu.8xlarge")
    CPU_16XL = ResourceBundle(name="16XL", description="4 CPU | 28GB RAM", id="cpu.16xlarge")
    GPU_S = ResourceBundle(
        name="GPU - S",
        description="1 x NVIDIA T4 | 16GB VRAM | 4 CPU | 16GB RAM",
        id="DRAWS_g4dn.xlarge_frac1_regular",
    )
    GPU_M = ResourceBundle(
        name="GPU - M",
        description="1 x NVIDIA T4 | 16GB VRAM | 8 CPU | 32GB RAM",
        id="DRAWS_g4dn.2xlarge_frac1_regular",
    )
    GPU_L = ResourceBundle(
        name="GPU - L",
        description="1 x NVIDIA A10G | 24GB VRAM | 8 CPU | 32GB RAM",
        id="DRAWS_g5.2xlarge_frac1_regular",
    )
    GPU_XL = ResourceBundle(
        name="GPU - XL",
        description="1 x NVIDIA L40S | 48GB VRAM | 4 CPU | 32GB RAM",
        id="DRAWS_g6e.xlarge_frac1_regular",
    )
    GPU_XXL = ResourceBundle(
        name="GPU - XXL",
        description="4 x NVIDIA A10G | 96GB VRAM | 48 CPU | 192GB RAM",
        id="DRAWS_g5.12xlarge_frac1_regular",
    )
    GPU_3XL = ResourceBundle(
        name="GPU - 3XL",
        description="4 x NVIDIA L40S | 192GB VRAM | 48 CPU | 384GB RAM",
        id="DRAWS_g6e.12xlarge_frac1_regular",
    )
    GPU_4XL = ResourceBundle(
        name="GPU - 4XL",
        description="8 x NVIDIA A10G | 192GB VRAM | 192 CPU | 768GB RAM",
        id="DRAWS_g5.48xlarge_frac1_regular",
    )
    GPU_5XL = ResourceBundle(
        name="GPU - 5XL",
        description="8 x NVIDIA L40S | 384GB VRAM | 192 CPU | 1.5TB RAM",
        id="DRAWS_g6e.48xlarge_frac1_regular",
    )


class PredictionEnvironmentPlatforms(StrEnum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREMISE = "onPremise"
    DATAROBOT = "datarobot"
    DATAROBOT_SERVERLESS = "datarobotServerless"
    OPEN_SHIFT = "openShift"
    OTHER = "other"
    SNOWFLAKE = "snowflake"
    SAP_AI_CORE = "sapAiCore"


class CustomModelArgs(Schema):
    resource_name: str
    name: str
    replicas: int | None = None
    description: str | None = None
    base_environment_id: str | None = None
    base_environment_version_id: str | None = None
    target_name: str | None = None
    target_type: str | None = None
    network_access: str | None = None
    runtime_parameter_values: list[drp.CustomModelRuntimeParameterValueArgs] | None = None
    files: list[tuple[str, str]] | None = None
    class_labels: list[str] | None = None
    negative_class_label: str | None = None
    positive_class_label: str | None = None
    folder_path: str | None = None
    memory_mb: int | None = None
    resource_bundle_id: str | None = None


class RegisteredModelArgs(Schema):
    resource_name: str
    name: str | None = None


class DeploymentArgs(Schema):
    resource_name: str
    label: str
    association_id_settings: drp.DeploymentAssociationIdSettingsArgs | None = None
    bias_and_fairness_settings: drp.DeploymentBiasAndFairnessSettingsArgs | None = None
    challenger_models_settings: drp.DeploymentChallengerModelsSettingsArgs | None = None
    challenger_replay_settings: drp.DeploymentChallengerReplaySettingsArgs | None = None
    drift_tracking_settings: drp.DeploymentDriftTrackingSettingsArgs | None = None
    health_settings: drp.DeploymentHealthSettingsArgs | None = None
    importance: str | None = None
    prediction_intervals_settings: drp.DeploymentPredictionIntervalsSettingsArgs | None = None
    prediction_warning_settings: drp.DeploymentPredictionWarningSettingsArgs | None = None
    predictions_by_forecast_date_settings: drp.DeploymentPredictionsByForecastDateSettingsArgs | None = None
    predictions_data_collection_settings: drp.DeploymentPredictionsDataCollectionSettingsArgs | None = None
    predictions_settings: drp.DeploymentPredictionsSettingsArgs | None = None
    segment_analysis_settings: drp.DeploymentSegmentAnalysisSettingsArgs | None = None


class PredictionEnvironmentArgs(Schema):
    resource_name: str
    name: str | None = None
    platform: PredictionEnvironmentPlatforms
