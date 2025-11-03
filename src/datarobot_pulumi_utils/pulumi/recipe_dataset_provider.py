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

from typing import Any, Dict, List, Optional

import datarobot as dr
import pulumi
from pulumi import Input
from pulumi.dynamic import CreateResult, ResourceProvider, UpdateResult

client = dr.Client()


class RecipeDatasetProvider(ResourceProvider):
    def create(self, props: Dict[str, Any]) -> CreateResult:
        use_case_id = props["use_case_id"]
        dataset_id = props["dataset_id"]
        dialect = props.get("dialect", dr.enums.DataWranglingDialect.SPARK)
        recipe_type = props.get("recipe_type", dr.enums.RecipeType.SQL)
        inputs: List[Dict[str, Any]] = props.get("inputs", [])
        query = props.get("query", None)
        name = props.get("name", "Unnamed Recipe Dataset")
        recipe_name = props.get("recipe_name", "Unnamed Recipe")

        # Get the use case and dataset objects
        use_case = dr.UseCase.get(use_case_id)
        dataset = dr.Dataset.get(dataset_id)

        # Create the recipe
        recipe = dr.models.Recipe.from_dataset(
            use_case=use_case,
            dataset=dataset,
            dialect=dialect,
            recipe_type=recipe_type,
        )

        client.put(
            f"recipes/{recipe.id}/inputs",
            json={"inputs": inputs},
        )

        recipe.set_recipe_metadata(recipe_id=recipe.id, metadata={"name": recipe_name, "sql": query or ""})

        recipe_dataset: dr.Dataset = dr.Dataset.create_from_recipe(recipe=recipe, use_cases=use_case_id, max_wait=7200)
        recipe_dataset.modify(name=name)

        outputs = {
            **props,
            "recipe_id": recipe.id,
            "status": recipe.status,
            "recipe_dataset_id": recipe_dataset.id,
        }
        return CreateResult(id_=recipe_dataset.id, outs=outputs)

    def delete(self, id: str, props: Dict[str, Any]) -> None:
        try:
            client.delete(f"useCases/{props['use_case_id']}/recipes/{props['recipe_id']}/?deleteResource=true")
            dr.Dataset.delete(dataset_id=id)
        except Exception:
            pass

    def update(self, id: str, olds: Dict[str, Any], news: Dict[str, Any]) -> UpdateResult:
        # If core properties changed, recreate the recipe
        if (
            olds.get("use_case_id") != news.get("use_case_id")
            or olds.get("dataset_id") != news.get("dataset_id")
            or olds.get("dialect") != news.get("dialect")
            or olds.get("recipe_type") != news.get("recipe_type")
            or olds.get("inputs") != news.get("inputs")
            or olds.get("query") != news.get("query")
        ):
            self.delete(id, olds)
            create_result = self.create(news)

            return UpdateResult(outs=create_result.outs)
        if olds.get("name") != news.get("name") or olds.get("recipe_name") != news.get("recipe_name"):
            if olds.get("name") != news.get("name"):
                recipe_dataset = dr.Dataset.get(id)
                recipe_dataset.modify(name=news["name"])
            if olds.get("recipe_name") != news.get("recipe_name"):
                recipe = dr.models.Recipe.get(news["recipe_id"])
                recipe.set_recipe_metadata(
                    recipe_id=recipe.id,
                    metadata={"name": news["recipe_name"]},
                )

        return UpdateResult(outs=news)


class RecipeDatasetResource(pulumi.dynamic.Resource):
    def __init__(
        self,
        name: str,
        use_case_id: Input[str],
        dataset_id: Input[str],
        dialect: Optional[Input[dr.enums.DataWranglingDialect]] = None,
        recipe_type: Optional[Input[dr.enums.RecipeType]] = None,
        inputs: Optional[Input[List[Dict[str, Any]]]] = None,
        query: Optional[Input[str]] = None,
        recipe_name: Optional[Input[str]] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        props = {
            "use_case_id": use_case_id,
            "dataset_id": dataset_id,
            "dialect": dialect,
            "recipe_type": recipe_type,
            "inputs": inputs,
            "query": query,
            "name": name,
            "recipe_name": recipe_name,
        }
        super().__init__(RecipeDatasetProvider(), name, props, opts)
