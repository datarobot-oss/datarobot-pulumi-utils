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

from datarobot_pulumi_utils.common import stack_outputs as so

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


def run(tmp_path: Path, outputs: dict[str, Any], *command: str) -> int:
    out_json = tmp_path / "outputs.json"
    out_json.write_text(json.dumps(outputs))
    return so.main(["--stack", "prod", "--outputs-json", str(out_json), *command])


def run_manifest(tmp_path: Path, manifest: str, outputs: dict[str, Any]) -> tuple[int, str]:
    path = tmp_path / ".datarobot.yaml"
    if not path.exists():
        path.write_text(manifest)
    code = run(tmp_path, outputs, "manifest", "--file", str(path))
    return code, path.read_text()


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


def test_dotenv_writes_only_the_named_outputs(tmp_path, capsys):
    outputs = {"DATAROBOT_USE_CASE_ID": "uc1", "MEMORY_SPACE_ID": "space", "MEM0_SPACE_ID": "m", "OTHER_ID": "x"}
    dotenv = tmp_path / ".env"
    dotenv.write_text("DATAROBOT_USE_CASE_ID=\nLLM_MODEL=k\n")
    args = ["dotenv", "DATAROBOT_USE_CASE_ID", "MEMORY_SPACE_ID", "--optional", "MEM0_SPACE_ID", "--file", str(dotenv)]
    assert run(tmp_path, outputs, *args) == 0
    assert dotenv.read_text() == "DATAROBOT_USE_CASE_ID=uc1\nLLM_MODEL=k\nMEMORY_SPACE_ID=space\nMEM0_SPACE_ID=m\n"
    assert "DATAROBOT_USE_CASE_ID=uc1" in capsys.readouterr().out


def test_dotenv_missing_optional_output_is_fine(tmp_path):
    dotenv = tmp_path / ".env"
    args = ["dotenv", "MEMORY_SPACE_ID", "--optional", "MEM0_SPACE_ID", "--file", str(dotenv)]
    assert run(tmp_path, {"MEMORY_SPACE_ID": "space"}, *args) == 0
    assert dotenv.read_text() == "MEMORY_SPACE_ID=space\n"


def test_dotenv_missing_output_leaves_file_alone(tmp_path):
    dotenv = tmp_path / ".env"
    dotenv.write_text("DATAROBOT_USE_CASE_ID=keep\n")
    args = ["dotenv", "DATAROBOT_USE_CASE_ID", "MEMORY_SPACE_ID", "--file", str(dotenv)]
    assert run(tmp_path, {"MEMORY_SPACE_ID": "space"}, *args) == 1
    assert dotenv.read_text() == "DATAROBOT_USE_CASE_ID=keep\n"


def test_dotenv_ignores_an_unknown_output():
    assert so.select_dotenv_outputs({"DATAROBOT_USE_CASE_ID": so.UNKNOWN}, ["DATAROBOT_USE_CASE_ID"]) == {}


def test_dotenv_fails_without_pulumi(tmp_path, monkeypatch):
    monkeypatch.setattr(so.shutil, "which", lambda _: None)
    dotenv = tmp_path / ".env"
    assert so.main(["--stack", "dev", "dotenv", "MEMORY_SPACE_ID", "--file", str(dotenv)]) == 1
    assert not dotenv.exists()


# manifest


def test_adds_env_shaped_outputs_sorted_and_quoted(tmp_path):
    code, text = run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "abc123", "A_FLAG": True, "PORT_N": 3})
    assert code == 0
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


def test_change_and_remove(tmp_path, capsys):
    run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "one", "OLD_ID": "x"})
    capsys.readouterr()
    code, text = run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "two"})
    out = capsys.readouterr()
    assert code == 0
    assert '"two"' in text and "OLD_ID" not in text
    assert "~ MEMORY_SPACE_ID=two (was one)" in out.out
    assert "- OLD_ID" in out.out


def test_removing_every_output_empties_the_block(tmp_path):
    run_manifest(tmp_path, MANIFEST, {"MEMORY_SPACE_ID": "one"})
    _, text = run_manifest(tmp_path, MANIFEST, {})
    assert text == MANIFEST


def test_idempotent(tmp_path, capsys):
    outputs = {"MEMORY_SPACE_ID": "abc", "MEM0_SPACE_ID": "def"}
    _, first = run_manifest(tmp_path, MANIFEST, outputs)
    capsys.readouterr()
    _, second = run_manifest(tmp_path, MANIFEST, outputs)
    out = capsys.readouterr()
    assert first == second
    assert "up to date (2 vars)" in out.out
    assert "WARNING" not in out.err


def test_the_use_case_becomes_the_top_level_use_case_id(tmp_path, capsys):
    outputs = {"DATAROBOT_USE_CASE_ID": "uc1", "MEMORY_SPACE_ID": "abc"}
    code, text = run_manifest(tmp_path, MANIFEST, outputs)
    assert code == 0
    assert text.startswith("name: my-agent\nuseCaseId: uc1\nartifact:\n")
    assert "DATAROBOT_USE_CASE_ID" not in text and "name: MEMORY_SPACE_ID\n" in text
    assert "~ useCaseId: uc1" in capsys.readouterr().out

    _, changed = run_manifest(tmp_path, MANIFEST, {**outputs, "DATAROBOT_USE_CASE_ID": "uc2"})
    assert changed == text.replace("uc1", "uc2")
    _, again = run_manifest(tmp_path, MANIFEST, {**outputs, "DATAROBOT_USE_CASE_ID": "uc2"})
    assert again == changed and "up to date" in capsys.readouterr().out


def test_entries_line_up_with_the_list_when_comments_were_reindented(tmp_path):
    shifted = MANIFEST.replace("              # >>>", "                # >>>").replace(
        "              # <<<", "                # <<<"
    )
    _, text = run_manifest(tmp_path, shifted, {"MEMORY_SPACE_ID": "abc"})
    assert "\n              - source: string\n                name: MEMORY_SPACE_ID\n" in text


def test_secret_skipped_with_warning(tmp_path, capsys):
    code, text = run_manifest(tmp_path, MANIFEST, {"API_TOKEN": "[secret]", "CRED_ID": "c1"})
    err = capsys.readouterr().err
    assert code == 0
    assert "API_TOKEN" not in text and "CRED_ID" in text
    assert "skipped API_TOKEN: it is a secret output" in err


def test_non_env_names_and_non_scalars_ignored(tmp_path, capsys):
    code, text = run_manifest(
        tmp_path,
        MANIFEST,
        {"memory_space_id": "a", "Mixed_Case": "b", "_X": "c", "NESTED": {"a": 1}, "NULLED": None},
    )
    err = capsys.readouterr().err
    assert code == 0 and text == MANIFEST
    assert "skipped NESTED" in err and "skipped NULLED" in err


def test_values_needing_quotes_round_trip(tmp_path, capsys):
    value = 'a: b # "c"\\d'
    run_manifest(tmp_path, MANIFEST, {"WEIRD": value})
    capsys.readouterr()
    run_manifest(tmp_path, MANIFEST, {"WEIRD": value})
    assert "up to date" in capsys.readouterr().out


def test_missing_markers_fails_and_leaves_file(tmp_path):
    manifest = MANIFEST.replace("              # <<< infra outputs\n", "")
    code, text = run_manifest(tmp_path, manifest, {"MEMORY_SPACE_ID": "abc"})
    assert code == 1 and text == manifest


def test_name_clash_fails(tmp_path, capsys):
    code, text = run_manifest(tmp_path, MANIFEST, {"LLM_MODEL": "other"})
    assert code == 1 and text == MANIFEST
    assert "LLM_MODEL declared both" in capsys.readouterr().err


def test_commented_names_do_not_clash(tmp_path):
    manifest = MANIFEST.replace(
        "              # >>>",
        "              # - source: string\n              #   name: MEM0_SPACE_ID\n              # >>>",
    )
    code, text = run_manifest(tmp_path, manifest, {"MEM0_SPACE_ID": "m"})
    assert code == 0 and "name: MEM0_SPACE_ID\n" in text


def test_empty_block_is_unchanged():
    new_text, previous, _ = so.update_manifest(MANIFEST, {})
    assert previous == {} and new_text == MANIFEST


def test_no_pulumi_leaves_manifest_when_allowed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(so.shutil, "which", lambda _: None)
    path = tmp_path / ".datarobot.yaml"
    path.write_text(MANIFEST)
    assert so.main(["--stack", "prod", "manifest", "--file", str(path), "--allow-missing-stack"]) == 0
    assert so.main(["--stack", "prod", "manifest", "--file", str(path)]) == 1
    assert path.read_text() == MANIFEST
    assert "pulumi is not on PATH" in capsys.readouterr().err


def test_skips_outputs_an_update_left_unknown():
    env, warnings = so.select_manifest_outputs({"MEMORY_SPACE_ID": so.UNKNOWN, "DATAROBOT_USE_CASE_ID": "uc1"}, "prod")
    assert env == {"DATAROBOT_USE_CASE_ID": "uc1"}
    assert len(warnings) == 1 and "MEMORY_SPACE_ID" in warnings[0] and "stack prod" in warnings[0]
