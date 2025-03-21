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
from typing import Any

import datarobot as dr

from pulumi_datarobot_utils.schema.base import Schema


class ApplicationTemplate(Schema):
    name: str

    @property
    def id(self) -> str:
        client = dr.client.get_client()

        try:
            templates = client.get(
                "customTemplates/", params={"templateType": "customApplicationTemplate"}
            ).json()
            template_id: str = next(
                template["id"]
                for template in templates["data"]
                if template["name"] == self.name
            )
            return template_id
        except Exception as e:
            raise ValueError(
                f"Could not find the Application Template ID for {self.name}"
            ) from e


class ApplicationTemplates(Enum):
    FLASK_APP_BASE = ApplicationTemplate(name="Flask App Base")
    Q_AND_A_CHAT_GENERATION_APP = ApplicationTemplate(name="Q&A Chat Generation App")
    SLACK_BOT_APP = ApplicationTemplate(name="Slack Bot App")
    STREAMLIT_APP_BASE = ApplicationTemplate(name="Streamlit App Base")
    NODE_JS_AND_REACT_APP = ApplicationTemplate(name="Node.js & React Base App")


class ApplicationSourceArgs(Schema):
    resource_name: str
    files: Any | None = None # TODO: let's actually try to find out the type here
    folder_path: str | None = None
    name: str | None = None


class QaApplicationArgs(Schema):
    resource_name: str
    name: str