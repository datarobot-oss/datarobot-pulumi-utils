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

from datarobot.enums import VectorDatabaseChunkingMethod, VectorDatabaseEmbeddingModel

from datarobot_pulumi_utils.schema.base import Field, Schema


class ChunkingParameters(Schema):
    embedding_model: VectorDatabaseEmbeddingModel | None = None
    chunking_method: VectorDatabaseChunkingMethod | None = None
    chunk_size: int | None = Field(ge=128, le=512)
    chunk_overlap_percentage: int | None = None
    separators: list[str] | None = None


class VectorDatabaseArgs(Schema):
    resource_name: str
    name: str | None = None
    chunking_parameters: ChunkingParameters


class VectorDatabaseSettings(Schema):
    max_documents_retrieved_per_prompt: int | None = None
    max_tokens: int | None = None
