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

import pulumi
from pydantic import Field, field_validator

from datarobot_pulumi_utils.schema.base import Schema


class ResourceBundle(Schema):
    id: str
    name: str
    description: str


class UseCaseArgs(Schema):
    resource_name: str
    name: str | None = None
    description: str | None = None
    opts: pulumi.ResourceOptions | None = None


class Schedule(Schema):
    day_of_months: list[str] = Field(
        description='List of the days of the month to run the schedule. Use ["*"] for every day.'
    )
    day_of_weeks: list[str] = Field(
        description='List of the days of the week to run the schedule. Use ["*"] for every day.'
    )
    hours: list[str] = Field(description='List of the hours to run the schedule. Use ["*"] for every hour.')
    minutes: list[str] = Field(description='List of the minutes to run the schedule. Use ["*"] for every minute.')
    months: list[str] = Field(
        description='List of the months of the year to run the schedule. Use ["*"] for every month.'
    )

    @field_validator("*")
    def validate_list(cls, v: list[str]) -> list[str]:
        for item in v:
            if item != "*" and not item.isdigit():
                raise ValueError(f"Invalid value {item}. Must be '*' or a digit.")
        return v
