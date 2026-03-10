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

from datarobot_pulumi_utils.schema.base import Field, Schema
from datarobot_pulumi_utils.schema.vectordb import VectorDatabaseSettings

CredentialType = Literal["azure", "aws", "google", "api"]


class LLMConfig(Schema):
    name: str
    credential_type: CredentialType


class LLMs:
    """
    Available LLM configurations
    """

    # Azure Models
    AZURE_OPENAI_GPT_5_CODEX = LLMConfig(name="azure-openai-gpt-5-codex", credential_type="azure")
    AZURE_OPENAI_GPT_5 = LLMConfig(name="azure-openai-gpt-5", credential_type="azure")
    AZURE_OPENAI_GPT_5_MINI = LLMConfig(name="azure-openai-gpt-5-mini", credential_type="azure")
    AZURE_OPENAI_GPT_5_NANO = LLMConfig(name="azure-openai-gpt-5-nano", credential_type="azure")
    AZURE_OPENAI_GPT_4_O = LLMConfig(name="azure-openai-gpt-4-o", credential_type="azure")
    AZURE_OPENAI_GPT_4_O_MINI = LLMConfig(name="azure-openai-gpt-4-o-mini", credential_type="azure")
    AZURE_OPENAI_GPT_4_TURBO = LLMConfig(name="azure-openai-gpt-4-turbo", credential_type="azure")
    AZURE_OPENAI_GPT_4_32K = LLMConfig(name="azure-openai-gpt-4-32k", credential_type="azure")
    AZURE_OPENAI_O4_MINI = LLMConfig(name="azure-openai-o4-mini", credential_type="azure")
    AZURE_OPENAI_GPT_4 = LLMConfig(name="azure-openai-gpt-4", credential_type="azure")
    AZURE_OPENAI_GPT_3_5_TURBO = LLMConfig(name="azure-openai-gpt-3.5-turbo", credential_type="azure")
    AZURE_OPENAI_GPT_3_5_TURBO_16K = LLMConfig(name="azure-openai-gpt-3.5-turbo-16k", credential_type="azure")
    AZURE_OPENAI_O3 = LLMConfig(name="azure-openai-o3", credential_type="azure")
    AZURE_OPENAI_O3_MINI = LLMConfig(name="azure-openai-o3-mini", credential_type="azure")
    AZURE_OPENAI_O1_MINI = LLMConfig(name="azure-openai-o1-mini", credential_type="azure")
    AZURE_OPENAI_O1 = LLMConfig(name="azure-openai-o1", credential_type="azure")
    # AWS Models
    AMAZON_NOVA_PREMIER = LLMConfig(name="amazon-nova-premier", credential_type="aws")
    AMAZON_NOVA_PRO = LLMConfig(name="amazon-nova-pro", credential_type="aws")
    AMAZON_NOVA_LITE = LLMConfig(name="amazon-nova-lite", credential_type="aws")
    AMAZON_NOVA_MICRO = LLMConfig(name="amazon-nova-micro", credential_type="aws")
    AMAZON_TITAN = LLMConfig(name="amazon-titan", credential_type="aws")
    AMAZON_ANTHROPIC_CLAUDE_OPUS_4_5_20251101_V1 = LLMConfig(
        name="amazon-anthropic-claude-opus-4-5-20251101-v1", credential_type="aws"
    )
    AMAZON_ANTHROPIC_CLAUDE_OPUS_4_1_V1 = LLMConfig(name="amazon-anthropic-claude-opus-4-1-v1", credential_type="aws")
    AMAZON_ANTHROPIC_CLAUDE_OPUS_4_20250514_V1 = LLMConfig(
        name="amazon-anthropic-claude-opus-4-20250514-v1", credential_type="aws"
    )
    AMAZON_ANTHROPIC_CLAUDE_SONNET_4_20250514_V1 = LLMConfig(
        name="amazon-anthropic-claude-sonnet-4-20250514-v1", credential_type="aws"
    )
    AMAZON_ANTHROPIC_CLAUDE_3_7_SONNET_V1 = LLMConfig(
        name="amazon-anthropic-claude-3-7-sonnet-v1", credential_type="aws"
    )
    AMAZON_ANTHROPIC_CLAUDE_3_5_SONNET_V2 = LLMConfig(
        name="amazon-anthropic-claude-3.5-sonnet-v2", credential_type="aws"
    )
    ANTHROPIC_CLAUDE_3_5_SONNET_V1 = LLMConfig(name="anthropic-claude-3.5-sonnet-v1", credential_type="api")
    AMAZON_ANTHROPIC_CLAUDE_3_5_HAIKU_V1 = LLMConfig(name="amazon-anthropic-claude-3-5-haiku-v1", credential_type="aws")
    ANTHROPIC_CLAUDE_3_OPUS = LLMConfig(name="anthropic-claude-3-opus", credential_type="aws")
    ANTHROPIC_CLAUDE_3_SONNET = LLMConfig(name="anthropic-claude-3-sonnet", credential_type="aws")
    ANTHROPIC_CLAUDE_3_HAIKU = LLMConfig(name="anthropic-claude-3-haiku", credential_type="aws")
    ANTHROPIC_CLAUDE_2 = LLMConfig(name="anthropic-claude-2", credential_type="aws")
    AMAZON_COHERE_COMMAND_R_PLUS_V1 = LLMConfig(name="amazon-cohere-command-r-plus-v1", credential_type="aws")
    AMAZON_COHERE_COMMAND_R_V1 = LLMConfig(name="amazon-cohere-command-r-v1", credential_type="aws")
    AMAZON_COHERE_COMMAND_TEXT_V14 = LLMConfig(name="amazon-cohere-command-text-v14", credential_type="aws")
    AMAZON_COHERE_COMMAND_LIGHT_TEXT_V14 = LLMConfig(name="amazon-cohere-command-light-text-v14", credential_type="aws")
    AMAZON_DEEPSEEK_R1_V1 = LLMConfig(name="amazon-deepseek-r1-v1", credential_type="aws")
    AMAZON_META_LLAMA_4_MAVERICK_17B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-4-maverick-17b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_4_SCOUT_17B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-4-scout-17b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_3_70B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-3-3-70b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_2_90B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-3-2-90b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_2_11B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-3-2-11b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_2_3B_INSTRUCT_V1 = LLMConfig(name="amazon-meta-llama-3-2-3b-instruct-v1", credential_type="aws")
    AMAZON_META_LLAMA_3_2_1B_INSTRUCT_V1 = LLMConfig(name="amazon-meta-llama-3-2-1b-instruct-v1", credential_type="aws")
    AMAZON_META_LLAMA_3_1_405B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-3-1-405b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_1_70B_INSTRUCT_V1 = LLMConfig(
        name="amazon-meta-llama-3-1-70b-instruct-v1", credential_type="aws"
    )
    AMAZON_META_LLAMA_3_1_8B_INSTRUCT_V1 = LLMConfig(name="amazon-meta-llama-3-1-8b-instruct-v1", credential_type="aws")
    AMAZON_META_LLAMA_3_8B_INSTRUCT_V1 = LLMConfig(name="amazon-meta-llama-3-8b-instruct-v1", credential_type="aws")
    AMAZON_META_LLAMA_3_70B_INSTRUCT_V1 = LLMConfig(name="amazon-meta-llama-3-70b-instruct-v1", credential_type="aws")
    AMAZON_MISTRAL_MISTRAL_LARGE_2402_V1 = LLMConfig(name="amazon-mistral-mistral-large-2402-v1", credential_type="aws")
    AMAZON_MISTRAL_MISTRAL_SMALL_2402_V1 = LLMConfig(name="amazon-mistral-mistral-small-2402-v1", credential_type="aws")
    AMAZON_MISTRAL_MISTRAL_7B_INSTRUCT_V0 = LLMConfig(
        name="amazon-mistral-mistral-7b-instruct-v0", credential_type="aws"
    )
    AMAZON_MISTRAL_MIXTRAL_8X7B_INSTRUCT_V0 = LLMConfig(
        name="amazon-mistral-mixtral-8x7b-instruct-v0", credential_type="aws"
    )
    AMAZON_NVIDIA_NEMOTRON_NANO_12B_V2 = LLMConfig(name="amazon-nvidia-nemotron-nano-12b-v2", credential_type="aws")
    AMAZON_NVIDIA_NEMOTRON_NANO_9B_V2 = LLMConfig(name="amazon-nvidia-nemotron-nano-9b-v2", credential_type="aws")
    AMAZON_OPENAI_GPT_OSS_120B = LLMConfig(name="amazon-openai-gpt-oss-120b", credential_type="aws")
    AMAZON_OPENAI_GPT_OSS_20B = LLMConfig(name="amazon-openai-gpt-oss-20b", credential_type="aws")
    # Google Models
    GOOGLE_CLAUDE_OPUS_4_1_20250805 = LLMConfig(name="google-claude-opus-4-1@20250805", credential_type="google")
    GOOGLE_CLAUDE_OPUS_4_20250514 = LLMConfig(name="google-claude-opus-4@20250514", credential_type="google")
    GOOGLE_CLAUDE_SONNET_4_20250514 = LLMConfig(name="google-claude-sonnet-4@20250514", credential_type="google")
    GOOGLE_CLAUDE_3_7_SONNET_20250219 = LLMConfig(name="google-claude-3-7-sonnet@20250219", credential_type="google")
    GOOGLE_CLAUDE_3_5_SONNET_V2_20241022 = LLMConfig(
        name="google-claude-3-5-sonnet-v2@20241022", credential_type="google"
    )
    GOOGLE_CLAUDE_3_5_SONNET_20240620 = LLMConfig(name="google-claude-3-5-sonnet@20240620", credential_type="google")
    GOOGLE_CLAUDE_3_5_HAIKU_20241022 = LLMConfig(name="google-claude-3-5-haiku@20241022", credential_type="google")
    GOOGLE_CLAUDE_3_OPUS_20240229 = LLMConfig(name="google-claude-3-opus@20240229", credential_type="google")
    GOOGLE_CLAUDE_3_HAIKU_20240307 = LLMConfig(name="google-claude-3-haiku@20240307", credential_type="google")
    GOOGLE_GEMINI_2_5_PRO = LLMConfig(name="google-gemini-2.5-pro", credential_type="google")
    GOOGLE_GEMINI_2_5_FLASH = LLMConfig(name="google-gemini-2.5-flash", credential_type="google")
    GOOGLE_GEMINI_2_0_FLASH = LLMConfig(name="google-gemini-2.0-flash", credential_type="google")
    GOOGLE_GEMINI_2_0_FLASH_LITE = LLMConfig(name="google-gemini-2.0-flash-lite", credential_type="google")
    GOOGLE_BISON = LLMConfig(name="google-bison", credential_type="google")
    GOOGLE_GEMINI_1_5_FLASH = LLMConfig(name="google-gemini-1.5-flash", credential_type="google")
    GOOGLE_1_5_PRO = LLMConfig(name="google-gemini-1.5-pro", credential_type="google")
    GOOGLE_LLAMA_4_MAVERICK_17B_128E_INSTRUCT_MAAS = LLMConfig(
        name="google-llama-4-maverick-17b-128e-instruct-maas", credential_type="google"
    )
    GOOGLE_LLAMA_4_SCOUT_17B_16E_INSTRUCT_MAAS = LLMConfig(
        name="google-llama-4-scout-17b-16e-instruct-maas", credential_type="google"
    )
    # Anthropic 1P Models
    ANTHROPIC_1P_CLAUDE_OPUS_4_5 = LLMConfig(name="anthropic-1p-claude-opus-4-5", credential_type="api")
    ANTHROPIC_1P_CLAUDE_OPUS_4_1 = LLMConfig(name="anthropic-1p-claude-opus-4-1", credential_type="api")
    ANTHROPIC_1P_CLAUDE_OPUS_4 = LLMConfig(name="anthropic-1p-claude-opus-4", credential_type="api")
    ANTHROPIC_1P_CLAUDE_SONNET_4 = LLMConfig(name="anthropic-1p-claude-sonnet-4", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_7_SONNET = LLMConfig(name="anthropic-1p-claude-3-7-sonnet", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_5_SONNET_V2 = LLMConfig(name="anthropic-1p-claude-3-5-sonnet-v2", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_5_SONNET_V1 = LLMConfig(name="anthropic-1p-claude-3-5-sonnet-v1", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_5_HAIKU = LLMConfig(name="anthropic-1p-claude-3-5-haiku", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_OPUS = LLMConfig(name="anthropic-1p-claude-3-opus", credential_type="api")
    ANTHROPIC_1P_CLAUDE_3_HAIKU = LLMConfig(name="anthropic-1p-claude-3-haiku", credential_type="api")
    # Cohere 1P Models
    COHERE_1P_COMMAND_R_PLUS_08_2024 = LLMConfig(name="cohere-1p-command-r-plus-08-2024", credential_type="api")
    COHERE_1P_COMMAND_R_08_2024 = LLMConfig(name="cohere-1p-command-r-08-2024", credential_type="api")
    COHERE_1P_COMMAND_A_03_2025 = LLMConfig(name="cohere-1p-command-a-03-2025", credential_type="api")
    COHERE_1P_COMMAND_R7B_12_2024 = LLMConfig(name="cohere-1p-command-r7b-12-2024", credential_type="api")
    # Cerebras Models
    CEREBRAS_QWEN_3_235B_A22B_INSTRUCT_2507 = LLMConfig(
        name="cerebras-qwen-3-235b-a22b-instruct-2507", credential_type="api"
    )
    CEREBRAS_QWEN_3_32B = LLMConfig(name="cerebras-qwen-3-32b", credential_type="api")
    CEREBRAS_LLAMA_4_SCOUT_17B_16E_INSTRUCT = LLMConfig(
        name="cerebras-llama-4-scout-17b-16e-instruct", credential_type="api"
    )
    CEREBRAS_LLAMA_33_70B = LLMConfig(name="cerebras-llama-33-70b", credential_type="api")
    CEREBRAS_LLAMA_31_8B = LLMConfig(name="cerebras-llama-31-8b", credential_type="api")
    # TogetherAI Models
    TOGETHERAI_ARCEE_AI_VIRTUOSO_LARGE = LLMConfig(name="togetherai-arcee-ai-virtuoso-large", credential_type="api")
    TOGETHERAI_ARCEE_AI_CODER_LARGE = LLMConfig(name="togetherai-arcee-ai-coder-large", credential_type="api")
    TOGETHERAI_ARCEE_AI_MAESTRO_REASONING = LLMConfig(
        name="togetherai-arcee-ai-maestro-reasoning", credential_type="api"
    )
    TOGETHERAI_GOOGLE_GEMMA_3N_E4B_INSTRUCT = LLMConfig(
        name="togetherai-google-gemma-3n-e4b-instruct", credential_type="api"
    )
    TOGETHERAI_MARIN_COMMUNITY_MARIN_8B_INSTRUCT = LLMConfig(
        name="togetherai-marin-community-marin-8b-instruct", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_4_MAVERICK_INSTRUCT_17BX128E = LLMConfig(
        name="togetherai-meta-llama-4-maverick-instruct-17bx128e", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_4_SCOUT_INSTRUCT_17BX16E = LLMConfig(
        name="togetherai-meta-llama-4-scout-instruct-17bx16e", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_3_70B_INSTRUCT_TURBO = LLMConfig(
        name="togetherai-meta-llama-3-3-70b-instruct-turbo", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_2_3B_INSTRUCT_TURBO = LLMConfig(
        name="togetherai-meta-llama-3-2-3b-instruct-turbo", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_1_405B_INSTRUCT_TURBO = LLMConfig(
        name="togetherai-meta-llama-3-1-405b-instruct-turbo", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_1_8B_INSTRUCT_TURBO = LLMConfig(
        name="togetherai-meta-llama-3-1-8b-instruct-turbo", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_70B_INSTRUCT_REFERENCE = LLMConfig(
        name="togetherai-meta-llama-3-70b-instruct-reference", credential_type="api"
    )
    TOGETHERAI_META_LLAMA_3_8B_INSTRUCT_LITE = LLMConfig(
        name="togetherai-meta-llama-3-8b-instruct-lite", credential_type="api"
    )
    TOGETHERAI_MISTRAL_SMALL_3_INSTRUCT_24B = LLMConfig(
        name="togetherai-mistral-small-3-instruct-24b", credential_type="api"
    )
    TOGETHERAI_MISTRAL_7B_INSTRUCT_V0_3 = LLMConfig(name="togetherai-mistral-7b-instruct-v0-3", credential_type="api")
    TOGETHERAI_MISTRAL_7B_INSTRUCT_V0_2 = LLMConfig(name="togetherai-mistral-7b-instruct-v0-2", credential_type="api")
    TOGETHERAI_MISTRAL_7B_INSTRUCT = LLMConfig(name="togetherai-mistral-7b-instruct", credential_type="api")
    TOGETHERAI_MISTRAL_MIXTRAL_8X7B_INSTRUCT_V0_1 = LLMConfig(
        name="togetherai-mistral-mixtral-8x7b-instruct-v0-1", credential_type="api"
    )

    # API Models
    DEPLOYED_LLM = LLMConfig(name="custom-model", credential_type="api")


class PlaygroundArgs(Schema):
    resource_name: str
    name: str | None = None


class LLMSettings(Schema):
    max_completion_length: int | None = None
    system_prompt: str | None = None
    temperature: float | None = Field(None, ge=0, le=1)
    top_p: float | None = Field(None, ge=0, le=1)


class LLMBlueprintArgs(Schema):
    resource_name: str
    description: str | None = None
    llm_id: str
    llm_settings: LLMSettings | None = None
    name: str | None = None
    prompt_type: str | None = None
    vector_database_settings: VectorDatabaseSettings | None = None
