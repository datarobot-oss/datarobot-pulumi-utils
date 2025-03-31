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

import datarobot as dr

from datarobot_pulumi_utils.schema.base import Schema
from datarobot_pulumi_utils.schema.common import ResourceBundle


class CustomAppResourceBundles(Enum):
    CPU_XXS = ResourceBundle(name="XXS", description="1 CPU | 128MB RAM", id="cpu.nano")
    CPU_XS = ResourceBundle(name="XS", description="1 CPU | 256MB RAM", id="cpu.micro")
    CPU_S = ResourceBundle(name="S", description="1 CPU | 512MB RAM", id="cpu.small")
    CPU_M = ResourceBundle(name="M", description="1 CPU | 1GB RAM", id="cpu.medium")
    CPU_L = ResourceBundle(name="L", description="2 CPU | 1.5GB RAM", id="cpu.large")
    CPU_XL = ResourceBundle(name="XL", description="2 CPU | 2GB RAM", id="cpu.xlarge")
    CPU_XXL = ResourceBundle(name="2XL", description="2 CPU | 3GB RAM", id="cpu.2xlarge")
    CPU_3XL = ResourceBundle(name="3XL", description="2 CPU | 4GB RAM", id="cpu.3xlarge")
    CPU_4XL = ResourceBundle(name="4XL", description="2 CPU | 6GB RAM", id="cpu.4xlarge")
    CPU_5XL = ResourceBundle(name="5XL", description="2 CPU | 8GB RAM", id="cpu.5xlarge")
    CPU_6XL = ResourceBundle(name="6XL", description="2 CPU | 10GB RAM", id="cpu.6xlarge")
    CPU_7XL = ResourceBundle(name="7XL", description="2 CPU | 12GB RAM", id="cpu.7xlarge")
    CPU_8XL = ResourceBundle(name="8XL", description="2 CPU | 14GB RAM", id="cpu.8xlarge")


class ApplicationTemplate(Schema):
    name: str

    @property
    def id(self) -> str:
        client = dr.client.get_client()

        try:
            # TODO: Consider using Python SDK here:
            #   https://github.com/datarobot/public_api_client/blob/070241a9a21b5bf19ccaaa3163b59741a8c5f3d6/datarobot/models/custom_templates.py#L168-L177
            #   https://github.com/datarobot/public_api_client/blob/070241a9a21b5bf19ccaaa3163b59741a8c5f3d6/datarobot/models/custom_templates.py#L116
            templates = client.get("customTemplates/", params={"templateType": "customApplicationTemplate"}).json()
            template_id: str = next(template["id"] for template in templates["data"] if template["name"] == self.name)
            return template_id
        except Exception as e:
            raise ValueError(f"Could not find the Application Template ID for {self.name}") from e


class ApplicationTemplates(Enum):
    FLASK_APP_BASE = ApplicationTemplate(name="Flask App Base")
    Q_AND_A_CHAT_GENERATION_APP = ApplicationTemplate(name="Q&A Chat Generation App")
    SLACK_BOT_APP = ApplicationTemplate(name="Slack Bot App")
    STREAMLIT_APP_BASE = ApplicationTemplate(name="Streamlit App Base")
    NODE_JS_AND_REACT_APP = ApplicationTemplate(name="Node.js & React Base App")


class ApplicationSourceArgs(Schema):
    resource_name: str
    base_environment_id: str
    files: Any | None = None  # TODO: let's actually try to find out the type here
    folder_path: str | None = None
    name: str | None = None


class QaApplicationArgs(Schema):
    resource_name: str
    name: str
