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
from typing import Any

import pulumi
import pulumi_datarobot as datarobot
from datarobot.enums import VectorDatabaseChunkingMethod, VectorDatabaseEmbeddingModel
from pydantic import BaseModel, ConfigDict, Field

from .globals import (
    GlobalPredictionEnvironmentPlatforms,
)

class UseCaseArgs(BaseModel):
    resource_name: str
    name: str | None = None
    description: str | None = None
    opts: pulumi.ResourceOptions | None = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ResourceBundleSize(str, Enum):
    XXS = "cpu.nano"
    XS = "cpu.micro"
    S = "cpu.small"
    M = "cpu.medium"
    L = "cpu.large"
    XL = "cpu.xlarge"
    XXL = "cpu.2xlarge"
    XXXL = "cpu.3xlarge"
    XXXXL = "cpu.4xlarge"


class CustomModelArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource_name: str
    name: str
    replicas: int | None = None
    description: str | None = None
    base_environment_id: str | None = None
    base_environment_version_id: str | None = None
    target_name: str | None = None
    target_type: str | None = None
    network_access: str | None = None
    runtime_parameter_values: (
        list[datarobot.CustomModelRuntimeParameterValueArgs] | None
    ) = None
    files: list[tuple[str, str]] | None = None
    class_labels: list[str] | None = None
    negative_class_label: str | None = None
    positive_class_label: str | None = None
    folder_path: str | None = None
    resource_bundle_id: str | None = None


class RegisteredModelArgs(BaseModel):
    resource_name: str
    name: str | None = None


class DeploymentArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource_name: str
    label: str
    association_id_settings: datarobot.DeploymentAssociationIdSettingsArgs | None = None
    bias_and_fairness_settings: (
        datarobot.DeploymentBiasAndFairnessSettingsArgs | None
    ) = None
    challenger_models_settings: (
        datarobot.DeploymentChallengerModelsSettingsArgs | None
    ) = None
    challenger_replay_settings: (
        datarobot.DeploymentChallengerReplaySettingsArgs | None
    ) = None
    drift_tracking_settings: datarobot.DeploymentDriftTrackingSettingsArgs | None = None
    health_settings: datarobot.DeploymentHealthSettingsArgs | None = None
    importance: str | None = None
    prediction_intervals_settings: (
        datarobot.DeploymentPredictionIntervalsSettingsArgs | None
    ) = None
    prediction_warning_settings: (
        datarobot.DeploymentPredictionWarningSettingsArgs | None
    ) = None
    predictions_by_forecast_date_settings: (
        datarobot.DeploymentPredictionsByForecastDateSettingsArgs | None
    ) = None
    predictions_data_collection_settings: (
        datarobot.DeploymentPredictionsDataCollectionSettingsArgs | None
    ) = None
    predictions_settings: datarobot.DeploymentPredictionsSettingsArgs | None = None
    segment_analysis_settings: (
        datarobot.DeploymentSegmentAnalysisSettingsArgs | None
    ) = None


class PredictionEnvironmentArgs(BaseModel):
    resource_name: str
    name: str | None = None
    platform: GlobalPredictionEnvironmentPlatforms


class CredentialArgs(BaseModel):
    resource_name: str
    name: str | None = None


class ApplicationSourceArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource_name: str
    files: Any | None = None # TODO: let's actually try to find out the type here
    folder_path: str | None = None
    name: str | None = None


class PlaygroundArgs(BaseModel):
    resource_name: str
    name: str | None = None


class LLMSettings(BaseModel):
    max_completion_length: int = Field(le=512)
    system_prompt: str


class LLMBlueprintArgs(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    resource_name: str
    description: str | None = None
    llm_id: str
    llm_settings: datarobot.LlmBlueprintLlmSettingsArgs | None = None
    name: str | None = None
    prompt_type: str | None = None
    vector_database_settings: datarobot.LlmBlueprintVectorDatabaseSettingsArgs | None = None


class ChunkingParameters(BaseModel):
    embedding_model: VectorDatabaseEmbeddingModel | None = None
    chunking_method: VectorDatabaseChunkingMethod | None = None
    chunk_size: int | None = Field(ge=128, le=512)
    chunk_overlap_percentage: int | None = None
    separators: list[str] | None = None


class VectorDatabaseArgs(BaseModel):
    resource_name: str
    name: str | None = None
    chunking_parameters: ChunkingParameters


class DatasetArgs(BaseModel):
    resource_name: str
    name: str | None = None
    file_path: str


class VectorDatabaseSettings(BaseModel):
    max_documents_retrieved_per_prompt: int | None = None
    max_tokens: int | None = None


class QaApplicationArgs(BaseModel):
    resource_name: str
    name: str
