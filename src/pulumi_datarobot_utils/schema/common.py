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

from typing import Union

import pulumi

from pulumi_datarobot_utils.schema.base import Schema


class ResourceBundle(Schema):
    id: str
    name: str
    description: str


class UseCaseArgs(Schema):
    resource_name: str
    name: str | None = None
    description: str | None = None
    opts: pulumi.ResourceOptions | None = None


CronExpr = Union[str, int]


class Schedule(Schema):
    day_of_month: list[CronExpr] = ["*"]
    day_of_week: list[CronExpr] = ["*"]
    hour: list[CronExpr] = ["*"]
    minute: list[CronExpr] = ["*"]
    month: list[CronExpr] = ["*"]
