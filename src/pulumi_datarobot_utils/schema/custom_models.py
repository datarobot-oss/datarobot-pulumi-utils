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
from enum import StrEnum

import pulumi_datarobot as drp

from pulumi_datarobot_utils.schema.base import Schema


# ('aws', 'gcp', 'azure', 'onPremise', 'datarobot', 'datarobotServerless', 'openShift', 'other', 'snowflake', 'sapAiCore')
class GlobalPredictionEnvironmentPlatforms(StrEnum):
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
    platform: GlobalPredictionEnvironmentPlatforms