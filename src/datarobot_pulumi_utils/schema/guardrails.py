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

from datarobot_pulumi_utils.schema.base import Schema, StrEnum


class GuardrailTemplateNames(StrEnum):
    CUSTOM_DEPLOYMENT = "Custom Deployment"
    FAITHFULNESS = "Faithfulness"
    PII_DETECTION = "PII Detection"
    PROMPT_INJECTION = "Prompt Injection"
    ROUGE_1 = "Rouge 1"
    SENTIMENT_CLASSIFIER = "Sentiment Classifier"
    STAY_ON_TOPIC_FOR_INPUTS = "Stay on topic for inputs"
    STAY_ON_TOPIC_FOR_OUTPUTS = "Stay on topic for output"
    TOXICITY = "Toxicity"
    RESPONSE_TOKENS = "Response Tokens"
    PROMPT_TOKENS = "Prompt Tokens"


class GuardrailModelNames(StrEnum):
    TOXICITY = "[Hugging Face] Toxicity Classifier"
    SENTIMENT = "[Hugging Face] Sentiment Classifier"
    REFUSAL = "[DataRobot] LLM Refusal Score"
    PROMPT_INJECTION = "[Hugging Face] Prompt Injection Classifier"


class Stage(StrEnum):
    PROMPT = "prompt"
    RESPONSE = "response"


class ModerationAction(StrEnum):
    BLOCK = "block"
    REPORT = "report"
    REPORT_AND_BLOCK = "reportAndBlock"


class GuardConditionComparator(StrEnum):
    """The comparator used in a guard condition."""

    GREATER_THAN = "greaterThan"
    LESS_THAN = "lessThan"
    EQUALS = "equals"
    NOT_EQUALS = "notEquals"
    IS = "is"
    IS_NOT = "isNot"
    MATCHES = "matches"
    DOES_NOT_MATCH = "doesNotMatch"
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "doesNotContain"


class Condition(Schema):
    comparand: float | str | bool | list[str]
    comparator: GuardConditionComparator


class Intervention(Schema):
    action: ModerationAction
    condition: str
    message: str


class GuardrailTemplate(Schema):
    template_name: str
    registered_model_name: str | None = None
    name: str
    stages: list[Stage]
    intervention: Intervention


class CustomModelGuardConfigurationArgs(Schema):
    name: str
    stages: list[Stage]
    template_name: GuardrailTemplateNames
    intervention: Intervention
    input_column_name: str | None = None
    output_column_name: str | None = None
