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
import json
from pathlib import Path
from typing import Any

import pulumi
import pytest

from datarobot_pulumi_utils.pulumi import stack_outputs as so

MANIFEST = """\
name: my-agent
artifact:
  spec:
    containerGroups:
      - containers:
          - name: main
            environmentVars:
              - source: api-key
              - source: string
                name: LLM_MODEL
                value: some-model
              # >>> infra outputs: written by `task infra:env`. Don't edit by hand.
              # <<< infra outputs
            port: 8080
"""


class _Mocks(pulumi.runtime.Mocks):
    def new_resource(self, args: pulumi.runtime.MockResourceArgs) -> tuple[str, dict[str, Any]]:
        return f"{args.name}-id", args.inputs

    def call(self, args: pulumi.runtime.MockCallArgs) -> dict[str, Any]:
        return {}


@pytest.fixture(autouse=True)
def mocks() -> None:
    pulumi.runtime.set_mocks(_Mocks(), preview=False)


def run(write: Any, path: Path, outputs: dict[str, Any]) -> None:
    """Call ``write`` inside a Pulumi runtime and wait for it."""
    pulumi.runtime.test(lambda: write(path, outputs))()


def run_manifest(tmp_path: Path, manifest: str, outputs: dict[str, Any]) -> str:
    path = tmp_path / ".datarobot.yaml"
    if not path.exists():
        path.write_text(manifest)
    run(so.write_manifest, path, outputs)
    return path.read_text()


# dotenv


def test_appends_when_missing():
    assert so.set_dotenv("A=1", {"DATAROBOT_USE_CASE_ID": "uc1"}) == "A=1\nDATAROBOT_USE_CASE_ID=uc1\n"
    assert so.set_dotenv("", {"DATAROBOT_USE_CASE_ID": "uc1"}) == "DATAROBOT_USE_CASE_ID=uc1\n"


def test_replaces_in_place_and_drops_later_duplicates():
    text = "A=1\nexport DATAROBOT_USE_CASE_ID = old\nB=2\nDATAROBOT_USE_CASE_ID=older\n# DATAROBOT_USE_CASE_ID=x\n"
    assert so.set_dotenv(text, {"DATAROBOT_USE_CASE_ID": "uc1"}) == (
        "A=1\nexport DATAROBOT_USE_CASE_ID=uc1\nB=2\n# DATAROBOT_USE_CASE_ID=x\n"
    )


def test_leaves_similar_names_alone():
    text = "DATAROBOT_USE_CASE_ID_OLD=x\n"
    assert so.set_dotenv(text, {"DATAROBOT_USE_CASE_ID": "uc1"}) == text + "DATAROBOT_USE_CASE_ID=uc1\n"


def test_write_dotenv(tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text("DATAROBOT_USE_CASE_ID=\nLLM_MODEL=k\n")
    outputs = {"DATAROBOT_USE_CASE_ID": pulumi.Output.from_input("uc1"), "MEMORY_SPACE_ID": "space", "ON": True}
    run(so.write_dotenv, dotenv, outputs)
    assert dotenv.read_text() == "DATAROBOT_USE_CASE_ID=uc1\nLLM_MODEL=k\nMEMORY_SPACE_ID=space\nON=true\n"


def test_write_dotenv_creates_the_file(tmp_path):
    dotenv = tmp_path / ".env"
    run(so.write_dotenv, dotenv, {"MEMORY_SPACE_ID": "space"})
    assert dotenv.read_text() == "MEMORY_SPACE_ID=space\n"


def test_preview_writes_nothing(tmp_path):
    pulumi.runtime.set_mocks(_Mocks(), preview=True)
    dotenv = tmp_path / ".env"
    run(so.write_dotenv, dotenv, {"MEMORY_SPACE_ID": "space"})
    assert not dotenv.exists()


def test_secrets_are_skipped(tmp_path):
    dotenv = tmp_path / ".env"
    run(so.write_dotenv, dotenv, {"API_TOKEN": pulumi.Output.secret("s3cret"), "CRED_ID": "c1"})
    assert dotenv.read_text() == "CRED_ID=c1\n"


def test_names_must_be_env_shaped(tmp_path):
    with pytest.raises(ValueError, match="memory_space_id"):
        so.write_dotenv(tmp_path / ".env", {"memory_space_id": "a"})


# manifest


def test_adds_outputs_sorted_and_quoted(tmp_path):
    text = run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "abc123", "A_FLAG": True, "PORT_N": 3})
    assert (
        "              # >>> infra outputs: written by `task infra:env`. Don't edit by hand.\n"
        "              - source: string\n"
        "                name: A_FLAG\n"
        '                value: "true"\n'
        "              - source: string\n"
        "                name: MEMORY_SPACE_ID\n"
        '                value: "abc123"\n'
        "              - source: string\n"
        "                name: PORT_N\n"
        '                value: "3"\n'
        "              # <<< infra outputs\n"
        "            port: 8080\n"
    ) in text
    assert text.startswith(MANIFEST.split("              # >>>")[0])


def test_change_and_remove(tmp_path):
    run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "one", "OLD_ID": "x"})
    text = run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "two"})
    assert '"two"' in text and "OLD_ID" not in text
    assert so.describe_changes({"MEMORY_SPACE_ID": "one", "OLD_ID": "x"}, {"MEMORY_SPACE_ID": "two"}) == [
        "  ~ MEMORY_SPACE_ID=two (was one)",
        "  - OLD_ID",
    ]


def test_removing_every_output_empties_the_block(tmp_path):
    run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "one"})
    assert run_manifest(tmp_path, MANIFEST, {}) == MANIFEST


def test_idempotent(tmp_path):
    outputs = {"MEMORY_SPACE_ID": "abc", "MEM0_SPACE_ID": "def"}
    first = run_manifest(tmp_path, MANIFEST, outputs)
    assert run_manifest(tmp_path, MANIFEST, outputs) == first


def test_the_use_case_becomes_the_top_level_use_case_id(tmp_path):
    outputs = {"DATAROBOT_USE_CASE_ID": "uc1", "MEMORY_SPACE_ID": "abc"}
    text = run_manifest(tmp_path, MANIFEST, outputs)
    assert text.startswith("name: my-agent\nuseCaseId: uc1\nartifact:\n")
    assert "DATAROBOT_USE_CASE_ID" not in text and "name: MEMORY_SPACE_ID\n" in text
    changed = run_manifest(tmp_path, MANIFEST, {**outputs, "DATAROBOT_USE_CASE_ID": "uc2"})
    assert changed == text.replace("uc1", "uc2")


def test_entries_line_up_with_the_list_when_comments_were_reindented(tmp_path):
    shifted = MANIFEST.replace("              # >>>", "                # >>>").replace(
        "              # <<<", "                # <<<"
    )
    text = run_manifest(tmp_path, shifted, {"MEMORY_SPACE_ID": "abc"})
    assert "\n              - source: string\n                name: MEMORY_SPACE_ID\n" in text


def test_secret_and_non_scalar_outputs_skipped(tmp_path):
    outputs = {"API_TOKEN": pulumi.Output.secret("s3cret"), "NESTED": {"a": 1}, "NULLED": None, "CRED_ID": "c1"}
    text = run_manifest(tmp_path, MANIFEST, outputs)
    assert "s3cret" not in text and "NESTED" not in text and "NULLED" not in text
    assert "name: CRED_ID\n" in text


def test_values_needing_quotes_round_trip():
    value = 'a: b # "c"\\d'
    text, _ = so.update_manifest(MANIFEST, {"WEIRD": value})
    _, previous = so.update_manifest(text, {"WEIRD": value})
    assert previous == {"WEIRD": value}


def test_missing_markers_fails_and_leaves_file(tmp_path):
    manifest = MANIFEST.replace("              # <<< infra outputs\n", "")
    with pytest.raises(so.ManifestError):
        run_manifest(tmp_path, manifest, {"MEMORY_SPACE_ID": "abc"})
    assert (tmp_path / ".datarobot.yaml").read_text() == manifest


def test_name_clash_fails(tmp_path):
    with pytest.raises(so.ManifestError, match="LLM_MODEL declared both"):
        run_manifest(tmp_path, MANIFEST, {"LLM_MODEL": "other"})
    assert (tmp_path / ".datarobot.yaml").read_text() == MANIFEST


def test_commented_names_do_not_clash(tmp_path):
    manifest = MANIFEST.replace(
        "              # >>>",
        "              # - source: string\n              #   name: MEM0_SPACE_ID\n              # >>>",
    )
    assert "name: MEM0_SPACE_ID\n" in run_manifest(tmp_path, manifest, {"MEM0_SPACE_ID": "m"})


def test_empty_block_is_unchanged():
    assert so.update_manifest(MANIFEST, {}) == (MANIFEST, {})
