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

from typing import Literal

import pulumi_datarobot as drp

from pulumi_datarobot_utils.schema.base import Field, Schema

CredentialType = Literal["azure", "aws", "google", "api"]


class LLMConfig(Schema):
    name: str
    credential_type: CredentialType


class LLMs:
    """
    Available LLM configurations
    """

    # Azure Models
    AZURE_OPENAI_GPT_3_5_TURBO = LLMConfig(
        name="azure-openai-gpt-3.5-turbo",
        credential_type="azure",
    )
    AZURE_OPENAI_GPT_3_5_TURBO_16K = LLMConfig(name="azure-openai-gpt-3.5-turbo-16k", credential_type="azure")
    AZURE_OPENAI_GPT_4 = LLMConfig(name="azure-openai-gpt-4", credential_type="azure")
    AZURE_OPENAI_GPT_4_32K = LLMConfig(name="azure-openai-gpt-4-32k", credential_type="azure")
    AZURE_OPENAI_GPT_4_TURBO = LLMConfig(name="azure-openai-gpt-4-turbo", credential_type="azure")
    AZURE_OPENAI_GPT_4_O = LLMConfig(name="azure-openai-gpt-4-o", credential_type="azure")
    AZURE_OPENAI_GPT_4_O_MINI = LLMConfig(name="azure-openai-gpt-4-o-mini", credential_type="azure")
    # AWS Models
    AMAZON_TITAN = LLMConfig(name="amazon-titan", credential_type="aws")
    ANTHROPIC_CLAUDE_2 = LLMConfig(name="anthropic-claude-2", credential_type="aws")
    ANTHROPIC_CLAUDE_3_HAIKU = LLMConfig(name="anthropic-claude-3-haiku", credential_type="aws")
    ANTHROPIC_CLAUDE_3_SONNET = LLMConfig(name="anthropic-claude-3-sonnet", credential_type="aws")
    ANTHROPIC_CLAUDE_3_OPUS = LLMConfig(name="anthropic-claude-3-opus", credential_type="aws")
    # Google Models
    GOOGLE_BISON = LLMConfig(name="google-bison", credential_type="google")
    GOOGLE_GEMINI_1_5_FLASH = LLMConfig(name="google-gemini-1.5-flash", credential_type="google")
    GOOGLE_1_5_PRO = LLMConfig(name="google-gemini-1.5-pro", credential_type="google")

    # API Models
    DEPLOYED_LLM = LLMConfig(name="custom-model", credential_type="api")


class PlaygroundArgs(Schema):
    resource_name: str
    name: str | None = None


class LLMSettings(Schema):
    system_prompt: str
    max_completion_length: int = Field(le=512)


class LLMBlueprintArgs(Schema):
    resource_name: str
    description: str | None = None
    llm_id: str
    llm_settings: drp.LlmBlueprintLlmSettingsArgs | None = None
    name: str | None = None
    prompt_type: str | None = None
    vector_database_settings: drp.LlmBlueprintVectorDatabaseSettingsArgs | None = None
