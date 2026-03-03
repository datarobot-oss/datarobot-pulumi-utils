# Copyright 2026 DataRobot, Inc.
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
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from datarobot_pulumi_utils.pulumi.papermill import PapermillProvider


@pytest.fixture(autouse=True)
def mock_pulumi():
    with patch("datarobot_pulumi_utils.pulumi.papermill.pulumi") as m:
        yield m


@pytest.fixture
def provider():
    return PapermillProvider()


@pytest.fixture
def mock_nbformat():
    with patch("datarobot_pulumi_utils.pulumi.papermill.nbformat") as m:
        m.read.return_value = MagicMock()
        yield m


@pytest.fixture
def mock_notebook_client():
    with patch("datarobot_pulumi_utils.pulumi.papermill.NotebookClient") as m:
        yield m


class TestDiff:
    def test_changes_when_input_path_differs(self, provider):
        olds = {"input_path": "old.ipynb", "parameters": {}}
        news = {"input_path": "new.ipynb", "parameters": {}, "result_file": ""}

        result = provider.diff("id", olds, news)

        assert result.changes is True

    def test_changes_when_parameters_differ(self, provider):
        olds = {"input_path": "nb.ipynb", "parameters": {"a": 1}}
        news = {"input_path": "nb.ipynb", "parameters": {"a": 2}, "result_file": ""}

        result = provider.diff("id", olds, news)

        assert result.changes is True

    def test_no_changes_when_same_and_result_file_exists(self, provider, tmp_path: Path):
        result_file = tmp_path / "result.yaml"
        result_file.touch()
        olds = {"input_path": "nb.ipynb", "parameters": {}}
        news = {"input_path": "nb.ipynb", "parameters": {}, "result_file": str(result_file)}

        result = provider.diff("id", olds, news)

        assert result.changes is False

    def test_changes_when_result_file_missing(self, provider, tmp_path: Path):
        olds = {"input_path": "nb.ipynb", "parameters": {}}
        news = {"input_path": "nb.ipynb", "parameters": {}, "result_file": str(tmp_path / "missing.yaml")}

        result = provider.diff("id", olds, news)

        assert result.changes is True


class TestExecuteNotebook:
    def test_missing_input_raises(self, provider, tmp_path: Path):
        props = {
            "input_path": str(tmp_path / "nonexistent.ipynb"),
            "result_file": str(tmp_path / "result.yaml"),
        }

        with pytest.raises(Exception, match="Input notebook not found"):
            provider._execute_notebook(props)

    def test_parameters_set_as_env_vars(self, provider, tmp_path: Path, mock_nbformat, mock_notebook_client):
        nb_path = tmp_path / "test.ipynb"
        nb_path.touch()
        result_file = tmp_path / "result.yaml"
        result_file.write_text("key: value\n", encoding="utf-8")

        props = {
            "input_path": str(nb_path),
            "result_file": str(result_file),
            "parameters": {"PAPERMILL_TEST_VAR": "hello", "PAPERMILL_TEST_NUM": "42"},
        }
        provider._execute_notebook(props)

        assert os.environ.get("PAPERMILL_TEST_VAR") == "hello"
        assert os.environ.get("PAPERMILL_TEST_NUM") == "42"

    def test_notebook_read_and_executed(self, provider, tmp_path: Path, mock_nbformat, mock_notebook_client):
        nb_path = tmp_path / "test.ipynb"
        nb_path.touch()
        result_file = tmp_path / "result.yaml"
        result_file.write_text("key: value\n", encoding="utf-8")

        props = {
            "input_path": str(nb_path),
            "result_file": str(result_file),
            "parameters": {},
        }
        result = provider._execute_notebook(props)

        mock_nbformat.read.assert_called_once_with(str(nb_path), as_version=4)
        mock_notebook_client.return_value.execute.assert_called_once()
        assert result.outs["result"] == {"key": "value"}

    def test_output_written_when_output_path_given(self, provider, tmp_path: Path, mock_nbformat, mock_notebook_client):
        nb_path = tmp_path / "test.ipynb"
        nb_path.touch()
        result_file = tmp_path / "result.yaml"
        result_file.write_text("{}", encoding="utf-8")
        output_path = tmp_path / "output.ipynb"

        props = {
            "input_path": str(nb_path),
            "output_path": str(output_path),
            "result_file": str(result_file),
            "parameters": {},
        }
        provider._execute_notebook(props)

        mock_nbformat.write.assert_called_once()

    def test_output_not_written_without_output_path(self, provider, tmp_path: Path, mock_nbformat, mock_notebook_client):
        nb_path = tmp_path / "test.ipynb"
        nb_path.touch()
        result_file = tmp_path / "result.yaml"
        result_file.write_text("{}", encoding="utf-8")

        props = {
            "input_path": str(nb_path),
            "result_file": str(result_file),
            "parameters": {},
        }
        provider._execute_notebook(props)

        mock_nbformat.write.assert_not_called()

    def test_empty_result_file_created_when_missing(self, provider, tmp_path: Path, mock_nbformat, mock_notebook_client):
        nb_path = tmp_path / "test.ipynb"
        nb_path.touch()
        result_file = tmp_path / "result.yaml"  # does not exist yet

        props = {
            "input_path": str(nb_path),
            "result_file": str(result_file),
            "parameters": {},
        }
        result = provider._execute_notebook(props)

        assert result_file.is_file()
        assert result.outs["result"] == {}
