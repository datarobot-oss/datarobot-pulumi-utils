from pathlib import Path
import json
from unittest.mock import patch, MagicMock
from datarobot_pulumi_utils.pulumi import ExportCollector
import pulumi

# This is a structural test (won't actually run in a normal test runner without Pulumi engine),
# but demonstrates invocation shape.

@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_basic(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to not be in dry run mode
    mock_is_dry_run.return_value = False

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output that immediately triggers apply
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        # When apply is called, immediately call the function with the resolved value
        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Create the ExportCollector instance
    c = ExportCollector(output_path=output_file, skip_preview=False)

    # Call the export method
    c.export("val1", "abc")

    # Finalize to write the outputs to the file
    c.finalize()

    # Verify that pulumi.export was called
    assert mock_export.called, "pulumi.export was not called."

    # Verify that from_input was called with the correct value
    mock_from_input.assert_called_with("abc")

    # Validate the file output
    assert output_file.exists(), "Output file was not created."
    with output_file.open() as f:
        data = json.load(f)
        assert data == {"val1": "abc"}, f"Expected {{'val1': 'abc'}}, got {data}"


@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_multiple_exports(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to not be in dry run mode
    mock_is_dry_run.return_value = False

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output that immediately triggers apply
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        # When apply is called, immediately call the function with the resolved value
        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Create the ExportCollector instance
    c = ExportCollector(output_path=output_file, skip_preview=False)

    # Call the export method multiple times
    c.export("val1", "abc")
    c.export("val2", 123)
    c.export("val3", {"nested": "data"})

    # Finalize to write the outputs to the file
    c.finalize()

    # Verify that pulumi.export was called for each export
    assert mock_export.call_count == 3, f"Expected 3 calls to pulumi.export, got {mock_export.call_count}"

    # Validate the file output
    assert output_file.exists(), "Output file was not created."
    with output_file.open() as f:
        data = json.load(f)
        expected = {"val1": "abc", "val2": 123, "val3": {"nested": "data"}}
        assert data == expected, f"Expected {expected}, got {data}"


@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_subset_filter(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to not be in dry run mode
    mock_is_dry_run.return_value = False

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output that immediately triggers apply
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        # When apply is called, immediately call the function with the resolved value
        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Create the ExportCollector instance
    c = ExportCollector(output_path=output_file, skip_preview=False)

    # Call the export method multiple times
    c.export("val1", "abc")
    c.export("val2", 123)
    c.export("val3", {"nested": "data"})

    # Finalize with subset filter
    c.finalize(subset=["val1", "val3"])

    # Validate the file output contains only subset
    assert output_file.exists(), "Output file was not created."
    with output_file.open() as f:
        data = json.load(f)
        expected = {"val1": "abc", "val3": {"nested": "data"}}
        assert data == expected, f"Expected {expected}, got {data}"


@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_skip_preview(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to be in dry run mode
    mock_is_dry_run.return_value = True

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Create the ExportCollector instance with skip_preview=True (default)
    c = ExportCollector(output_path=output_file, skip_preview=True)

    # Call the export method
    c.export("val1", "abc")

    # Finalize - should skip due to dry run
    c.finalize()

    # File should not exist due to preview mode
    assert not output_file.exists(), "Output file should not be created during preview."


@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_force_preview(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to be in dry run mode
    mock_is_dry_run.return_value = True

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Create the ExportCollector instance
    c = ExportCollector(output_path=output_file, skip_preview=True)

    # Call the export method
    c.export("val1", "abc")

    # Finalize with force=True - should write despite dry run
    c.finalize(force=True)

    # File should exist due to force=True
    assert output_file.exists(), "Output file should be created when force=True."
    with output_file.open() as f:
        data = json.load(f)
        assert data == {"val1": "abc"}, f"Expected {{'val1': 'abc'}}, got {data}"


@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.from_input')
@patch('pulumi.export')
def test_collector_redactor(mock_export, mock_from_input, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to not be in dry run mode
    mock_is_dry_run.return_value = False

    output_file = tmp_path / "test_output.json"

    # Mock Output.from_input to return a mock output
    def create_mock_output(value):
        mock_output = MagicMock()
        mock_output.apply = MagicMock()

        def mock_apply(func):
            result = func(value)
            return result
        mock_output.apply.side_effect = mock_apply
        return mock_output

    mock_from_input.side_effect = create_mock_output

    # Define a redactor that masks secret values
    def redactor(key, value):
        if "secret" in key.lower():
            return "***REDACTED***"
        return value

    # Create the ExportCollector instance with redactor
    c = ExportCollector(output_path=output_file, skip_preview=False, redactor=redactor)

    # Call the export method
    c.export("api_key", "abc123")
    c.export("secret_token", "secret123")
    c.export("public_url", "https://example.com")

    # Finalize to write the outputs to the file
    c.finalize()

    # Validate the file output has redacted secret values
    assert output_file.exists(), "Output file was not created."
    with output_file.open() as f:
        data = json.load(f)
        expected = {
            "api_key": "abc123",
            "secret_token": "***REDACTED***",
            "public_url": "https://example.com"
        }
        assert data == expected, f"Expected {expected}, got {data}"
