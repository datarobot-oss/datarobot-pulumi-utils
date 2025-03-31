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

import sys
from typing import Any, Literal, Union

if sys.version_info >= (3, 12):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

from datarobot_pulumi_utils.schema.base import Field, Schema, StrEnum


class ChunkSizeTypes(StrEnum):
    AUTO = "auto"
    FIXED = "fixed"
    DYNAMIC = "dynamic"


class BatchPredictionJobRemapping(Schema):
    pass  # TODO: no fields? Should we define some?


class BatchPredictionJobCSVSettings(Schema):
    delimiter: str = ","
    encoding: str = "utf-8"
    quotechar: str = '"'


class AzureIntake(Schema):
    type: Literal["azure"]


class BigQueryIntake(Schema):
    type: Literal["bigQuery"]


class DataStageIntake(Schema):
    type: Literal["dataStage"]


class Catalog(Schema):
    type: Literal["dataset"]
    datasetId: str


class DSSIntake(Schema):
    type: Literal["dss"]


class FileSystemIntake(Schema):
    type: Literal["fileSystem"]


class GCPIntake(Schema):
    type: Literal["gcp"]


class HTTPIntake(Schema):
    type: Literal["http"]


class JDBCIntake(Schema):
    type: Literal["jdbc"]
    dataStoreId: str
    catalog: str | None = None
    credentialId: str | None = None
    fetchSize: int | None = Field(default=1, ge=1, le=1_000_000)
    query: str | None = None
    db_schema: str | None = Field(default=None, alias="schema")
    table: str | None = None


class LocalFileIntake(Schema):
    type: Literal["localFile"]


class S3Intake(Schema):
    type: Literal["s3"]


class SnowflakeIntake(Schema):
    type: Literal["snowflake"]


class SynapseIntake(Schema):
    type: Literal["synapse"]


class AzureOutput(Schema):
    type: Literal["azure"] = "azure"
    credentialId: str
    url: str
    format: str = "csv"
    partitionColumns: list[str] = Field(default_factory=list)


PredictionIntake = Union[
    AzureIntake,
    BigQueryIntake,
    DataStageIntake,
    Catalog,
    DSSIntake,
    FileSystemIntake,
    GCPIntake,
    HTTPIntake,
    JDBCIntake,
    LocalFileIntake,
    S3Intake,
    SnowflakeIntake,
    SynapseIntake,
]


class BigQueryOutput(Schema):
    type: Literal["bigQuery"]


class FileSystemOutput(Schema):
    type: Literal["fileSystem"]


class GCPOutput(Schema):
    type: Literal["gcp"]


class HTTPOutput(Schema):
    type: Literal["http"]


class JDBCOutput(Schema):
    type: Literal["jdbc"] = "jdbc"
    dataStoreId: str
    statementType: str
    table: str
    catalog: str | None = None
    commitInterval: int = Field(default=600, ge=0, le=86400)
    createTableIfNotExists: bool = False
    credentialId: str | None = None
    db_schema: str | None = Field(default=None, alias="schema")
    updateColumns: list[str] | None = Field(default_factory=lambda: [])
    whereColumns: list[str] | None = Field(default_factory=lambda: [])


class LocalFileOutput(Schema):
    type: Literal["localFile"]


class S3Output(Schema):
    type: Literal["s3"]


class SnowflakeOutput(Schema):
    type: Literal["snowflake"]


class SynapseOutput(Schema):
    type: Literal["synapse"]


class TableauOutput(Schema):
    type: Literal["tableau"]


PredictionOutput = Union[
    AzureOutput,
    BigQueryOutput,
    FileSystemOutput,
    GCPOutput,
    HTTPOutput,
    JDBCOutput,
    LocalFileOutput,
    S3Output,
    SnowflakeOutput,
    SynapseOutput,
    TableauOutput,
]


class BatchPredictionJobPredictionInstance(Schema):
    apiKey: str
    datarobotKey: str
    hostName: str
    sslEnabled: bool = True


class BatchJobTimeSeriesSettingsForecast(Schema):
    type: Literal["forecast"]
    forecastPoint: str
    relaxKnownInAdvanceFeaturesCheck: bool = False


class BatchPredictionJobTimeSeriesSettingsForecastWithPolicy(Schema):
    type: Literal["forecastWithPolicy"]


class BatchJobTimeSeriesSettingsHistorical(Schema):
    type: Literal["historical"]


TimeSeriesSettings = Union[
    BatchJobTimeSeriesSettingsForecast,
    BatchPredictionJobTimeSeriesSettingsForecastWithPolicy,
    BatchJobTimeSeriesSettingsHistorical,
]


class BatchPredictionJobDefinitionsCreate(Schema):
    abortOnError: bool = True
    chunkSize: ChunkSizeTypes | int = Field(default=ChunkSizeTypes.AUTO)
    columnNamesRemapping: list[BatchPredictionJobRemapping] = Field(default_factory=list)
    csvSettings: BatchPredictionJobCSVSettings = Field(default_factory=BatchPredictionJobCSVSettings)
    deploymentId: str
    disableRowLevelErrorHandling: bool = False
    enabled: bool = True
    explanationAlgorithm: str | None = None
    explanationClassNames: list[str] | None = None
    explanationNumTopClasses: int | None = Field(default=None, ge=1, le=10)
    includePredictionStatus: bool = False
    includeProbabilities: bool = True
    includeProbabilitiesClasses: list[str] = Field(default_factory=list)
    intake_settings: PredictionIntake = Field(..., discriminator="type")
    maxExplanations: int = Field(default=0, ge=0, le=100)
    modelId: str | None = None
    modelPackageId: str | None = None
    monitoringBatchPrefix: str | None = None
    num_concurrent: int = Field(default=1, ge=1)
    output_settings: PredictionOutput = Field(discriminator="type")
    passthroughColumns: list[str] | None = None
    passthroughColumnsSet: str = "all"
    pinnedModelId: str | None = None
    predictionInstance: BatchPredictionJobPredictionInstance | None = None
    predictionThreshold: float | None = Field(default=None, ge=0, le=1)
    predictionWarningEnabled: bool | None = None
    skipDriftTracking: bool = False
    thresholdHigh: float | None = None
    thresholdLow: float | None = None
    timeseriesSettings: TimeSeriesSettings | None = None


class BaselineValues(TypedDict, total=False):
    value: float


class CustomMetricArgs(Schema):
    name: str
    units: str
    is_model_specific: bool
    type: Any
    directionality: Any
    description: str | None = None
    baseline_values: list[BaselineValues] | None = None
    value_column_name: str | None = None
    sample_count_column_name: str | None = None
    timestamp_column_name: str | None = None
    timestamp_format: str | None = None
    batch_column_name: str | None = None
