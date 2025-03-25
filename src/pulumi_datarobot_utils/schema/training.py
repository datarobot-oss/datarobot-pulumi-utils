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
from __future__ import annotations

import datarobot as dr
from pydantic import ConfigDict

from pulumi_datarobot_utils.schema.base import Field, Schema, StrEnum
from pulumi_datarobot_utils.schema.common import Schedule


class CVMethod(StrEnum):
    RANDOM_CV = "RandomCV"
    STRATIFIED_CV = "StratifiedCV"


class Metric(StrEnum):
    ACCURACY = "Accuracy"
    AUC = "AUC"
    BALANCED_ACCURACY = "Balanced Accuracy"
    GINI_NORM = "Gini Norm"
    KOLMOGOROV_SMIRNOV = "Kolmogorov-Smirnov"
    LOG_LOSS = "LogLoss"
    RATE_AT_TOP5 = "Rate@Top5%"
    RATE_AT_TOP10 = "Rate@Top10%"
    TPR = "TPR"
    FPR = "FPR"
    TNR = "TNR"
    PPV = "PPV"
    NPV = "NPV"
    F1 = "F1"
    MCC = "MCC"
    FVE_BINOMIAL = "FVE Binomial"
    FVE_GAMMA = "FVE Gamma"
    FVE_POISSON = "FVE Poisson"
    FVE_TWEEDIE = "FVE Tweedie"
    GAMMA_DEVIANCE = "Gamma Deviance"
    MAE = "MAE"
    MAPE = "MAPE"
    POISSON_DEVIANCE = "Poisson Deviance"
    RSQUARED = "R Squared"
    RMSE = "RMSE"
    RMSLE = "RMSLE"
    TWEEDIE_DEVIANCE = "Tweedie Deviance"


class ValidationType(StrEnum):
    CV = "CV"
    TVH = "TVH"


class TriggerType(StrEnum):
    SCHEDULE = "schedule"
    DATA_DRIFT_DECLINE = "data_drift_decline"
    ACCURACY_DECLINE = "accuracy_decline"
    NONE = "None"


class ActionType(StrEnum):
    CREATE_CHALLENGER = "create_challenger"
    CREATE_MODEL_PACKAGE = "create_model_package"
    MODEL_REPLACEMENT = "model_replacement"


class FeatureListStrategy(StrEnum):
    INFORMATIVE_FEATURES = "informative_features"
    SAME_AS_CHAMPION = "same_as_champion"


class ModelSelectionStrategy(StrEnum):
    AUTOPILOT_RECOMMENDED = "autopilot_recommended"
    SAME_BLUEPRINT = "same_blueprint"
    SAME_HYPERPARAMETERS = "same_hyperparameters"


class ProjectOptionsStrategy(StrEnum):
    SAME_AS_CHAMPION = "same_as_champion"
    OVERRIDE_CHAMPION = "override_champion"
    CUSTOM = "custom"


class AutopilotOptions(Schema):
    blend_best_models: bool = True
    mode: dr.AUTOPILOT_MODE = dr.AUTOPILOT_MODE.QUICK
    run_leakage_removed_feature_list: bool = True
    scoring_code_only: bool = False
    shap_only_mode: bool = False


class TimeUnit(StrEnum):
    MILLISECOND = "MILLISECOND"
    # TODO: other units?


class Periodicity(Schema):
    time_steps: int = 0
    time_unit: TimeUnit = TimeUnit.MILLISECOND


class RetrainingTrigger(Schema):
    min_interval_between_runs: str | None = None
    schedule: Schedule = Field(default_factory=Schedule)
    status_declines_to_failing: bool = True
    status_declines_to_warning: bool = True
    status_still_in_decline: bool | None = True
    type: TriggerType = TriggerType.SCHEDULE


class ProjectOptions(Schema):
    cv_method: CVMethod = CVMethod.RANDOM_CV
    holdout_pct: float | None = None
    metric: Metric = Metric.ACCURACY
    reps: int | None = None
    validation_pct: float | None = None
    validation_type: ValidationType = ValidationType.CV


class TimeSeriesOptions(Schema):
    calendar_id: str | None = None
    differencing_method: str = "auto"
    exponentially_weighted_moving_alpha: int | None = None
    periodicities: list[Periodicity] | None = None
    treat_as_exponential: str | None = "auto"


class DeploymentRetrainingPolicyArgs(Schema):
    model_config = ConfigDict(protected_namespaces=())

    resource_name: str

    action: str | None = None
    autopilot_options: AutopilotOptions | None = None
    description: str | None = None
    feature_list_strategy: str | None = None
    model_selection_strategy: str | None = None
    name: str | None = None
    project_options: ProjectOptions | None = None
    project_options_strategy: str | None = None
    time_series_options: TimeSeriesOptions | None = None
    trigger: RetrainingTrigger | None = None
