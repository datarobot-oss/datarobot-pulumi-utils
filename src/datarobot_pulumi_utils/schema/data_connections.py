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
from datarobot.enums import DataDriverListTypes

from datarobot_pulumi_utils.schema.base import Schema


class ExternalDataDriver(Schema):
    canonical_name: str

    @property
    def id(self) -> str:
        try:
            drivers = dr.DataDriver.list(typ=DataDriverListTypes.ALL)
            matching_drivers = [
                driver
                for driver in drivers
                if driver.canonical_name and self.canonical_name.lower() in driver.canonical_name.lower()
            ]
            if not matching_drivers:
                raise ValueError(f"No driver found with canonical name containing {self.canonical_name}")

            latest_driver = max(
                (driver for driver in matching_drivers if driver.id is not None), key=lambda d: d.id or ""
            )
            if latest_driver.id is None:
                raise ValueError(f"Driver ID for {latest_driver.canonical_name} is None")
            return latest_driver.id
        except Exception as e:
            raise ValueError(f"Could not find the External Data Driver ID for {self.canonical_name}") from e


class ExternalDataDrivers(Enum):
    SAP_DATASPHERE = ExternalDataDriver(
        canonical_name="SAP Datasphere",
    )
    SAP_HANA = ExternalDataDriver(
        canonical_name="SAP HANA",
    )
