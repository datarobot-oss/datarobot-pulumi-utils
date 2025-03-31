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

from datetime import datetime
from typing import Any

import datarobot as dr
from pydantic import ConfigDict

from datarobot_pulumi_utils.schema.base import Schema, StrEnum
from datarobot_pulumi_utils.schema.common import Schedule


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
    mode: str = dr.AUTOPILOT_MODE.QUICK  # TODO: Pydantic doesn't work well with datarobot.enums
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
    schedule: Schedule | None = None
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


class CalendarArgs(Schema):
    name: str
    country_code: str
    start_date: str | datetime
    end_date: str | datetime


class DatetimePartitioningArgs(Schema):
    model_config = ConfigDict(protected_namespaces=())

    datetime_partition_column: str
    autopilot_data_selection_method: str | None = None
    validation_duration: str | None = None
    holdout_start_date: Any | None = None
    holdout_duration: str | None = None
    disable_holdout: bool | None = None
    gap_duration: str | None = None
    number_of_backtests: int | None = None
    backtests: Any | None = None
    use_time_series: bool = False
    default_to_known_in_advance: bool = False
    default_to_do_not_derive: bool = False
    feature_derivation_window_start: int | None = None
    feature_derivation_window_end: int | None = None
    feature_settings: Any | None = None
    forecast_window_start: int | None = None
    forecast_window_end: int | None = None
    windows_basis_unit: str | None = None
    treat_as_exponential: str | None = None
    differencing_method: str | None = None
    periodicities: Any | None = None
    multiseries_id_columns: list[str] | None = None
    use_cross_series_features: bool | None = None
    aggregation_type: str | None = None
    cross_series_group_by_columns: list[str] | None = None
    calendar_id: str | None = None
    holdout_end_date: Any | None = None
    unsupervised_mode: bool = False
    model_splits: int | None = None
    allow_partial_history_time_series_predictions: bool = False
    unsupervised_type: str | None = None


class AnalyzeAndModelArgs(Schema):
    target: Any | None = None
    mode: str = dr.AUTOPILOT_MODE.QUICK  # TODO: Pydantic doesn't work well with datarobot.enums
    metric: Any | None = None
    worker_count: Any | None = None
    positive_class: Any | None = None
    partitioning_method: Any | None = None
    featurelist_id: Any | None = None
    advanced_options: Any | None = None
    max_wait: int = dr.enums.DEFAULT_MAX_WAIT
    target_type: Any | None = None
    credentials: Any | None = None
    feature_engineering_prediction_point: Any | None = None
    unsupervised_mode: bool = False
    relationships_configuration_id: Any | None = None
    class_mapping_aggregation_settings: Any | None = None
    segmentation_task_id: Any | None = None
    unsupervised_type: Any | None = None
    autopilot_cluster_list: Any | None = None
    use_gpu: Any | None = None


class AdvancedOptionsArgs(Schema):
    model_config = ConfigDict(protected_namespaces=())

    weights: str | None = None
    response_cap: bool | float | None = None
    blueprint_threshold: int | None = None
    seed: int | None = None
    smart_downsampled: bool | None = None
    majority_downsampling_rate: float | None = None
    offset: list[str] | None = None
    exposure: str | None = None
    accuracy_optimized_mb: bool | None = None
    scaleout_modeling_mode: str | None = None
    events_count: str | None = None
    monotonic_increasing_featurelist_id: str | None = None
    monotonic_decreasing_featurelist_id: str | None = None
    only_include_monotonic_blueprints: bool | None = None
    allowed_pairwise_interaction_groups: list[tuple[str, ...]] | None = None
    blend_best_models: bool | None = None
    scoring_code_only: bool | None = None
    prepare_model_for_deployment: bool | None = None
    consider_blenders_in_recommendation: bool | None = None
    min_secondary_validation_model_count: int | None = None
    shap_only_mode: bool | None = None
    autopilot_data_sampling_method: str | None = None
    run_leakage_removed_feature_list: bool | None = None
    autopilot_with_feature_discovery: bool | None = False
    feature_discovery_supervised_feature_reduction: bool | None = None
    exponentially_weighted_moving_alpha: float | None = None
    external_time_series_baseline_dataset_id: str | None = None
    use_supervised_feature_reduction: bool | None = True
    primary_location_column: str | None = None
    protected_features: list[str] | None = None
    preferable_target_value: str | None = None
    fairness_metrics_set: str | None = None
    fairness_threshold: str | None = None
    bias_mitigation_feature_name: str | None = None
    bias_mitigation_technique: str | None = None
    include_bias_mitigation_feature_as_predictor_variable: bool | None = None
    default_monotonic_increasing_featurelist_id: str | None = None
    default_monotonic_decreasing_featurelist_id: str | None = None
    model_group_id: str | None = None
    model_regime_id: str | None = None
    model_baselines: list[str] | None = None
    incremental_learning_only_mode: bool | None = None
    incremental_learning_on_best_model: bool | None = None
    chunk_definition_id: str | None = None
    incremental_learning_early_stopping_rounds: int | None = None


class FeatureSettingConfig(Schema):
    feature_name: str
    known_in_advance: bool | None = None
    do_not_derive: bool | None = None


class AutopilotRunArgs(Schema):
    name: str
    create_from_dataset_config: dict[str, Any] | None = None
    analyze_and_model_config: AnalyzeAndModelArgs | None = None
    datetime_partitioning_config: DatetimePartitioningArgs | None = None
    feature_settings_config: list[FeatureSettingConfig] | None = None
    advanced_options_config: AdvancedOptionsArgs | None = None
    user_defined_segment_id_columns: list[str] | None = None
