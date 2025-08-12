from pathlib import Path
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pulumi.runtime import get_root_resource
from datarobot_pulumi_utils.pulumi import ExportCollector
import pulumi

# This is a structural test (won't actually run in a normal test runner without Pulumi engine),
# but demonstrates invocation shape.

@patch('pulumi.runtime.is_dry_run')
@patch('pulumi.Output.all')
@patch('pulumi.get_stack')
@patch('pulumi.runtime.get_root_resource')
@patch('pulumi.export')
def test_collector_basic(mock_export, mock_get_root_resource, mock_get_stack, mock_output_all, mock_is_dry_run, tmp_path):
    # Mock the Pulumi runtime to not be in dry run mode
    mock_is_dry_run.return_value = False

    # Mock the Pulumi stack
    mock_stack = MagicMock()
    mock_get_stack.return_value = mock_stack

    # Mock get_root_resource to return a valid Stack-like instance
    mock_root_resource = MagicMock()
    mock_root_resource.output = MagicMock()  # Ensure it has an `output` method
    mock_get_root_resource.return_value = mock_root_resource

    # Mock Output.all to immediately resolve the outputs
    def mock_apply_side_effect(func):
        resolved_data = {"val1": "abc", "val2": 123}
        return func(resolved_data)

    mock_aggregate = MagicMock()
    mock_aggregate.apply.side_effect = mock_apply_side_effect
    mock_output_all.return_value = mock_aggregate

    output_file = tmp_path / "test_output.json"

    # Mock the behavior of is_stack directly in the test logic
    def is_stack(resource):
        return resource == mock_root_resource

    # Configure the patched `pulumi.export`
    def patched_export(name, value):
        if not is_stack(mock_root_resource):
            raise Exception("Failed to export output. Root resource is not an instance of 'Stack'")
        mock_root_resource.output(name, value)

    mock_export.side_effect = patched_export

    # Create the ExportCollector instance
    c = ExportCollector(output_path=output_file, skip_preview=False)

    # Call the export method
    c.export("val1", "abc")

    # Finalize to write the outputs to the file
    c.finalize()

    # Verify that the output method was called correctly
    args, _ = mock_root_resource.output.call_args
    assert args[0] == "val1", "Exported key 'val1' not passed correctly."
    assert isinstance(args[1], pulumi.Output), "Exported value is not a Pulumi Output object."

    # Validate the file output
    assert output_file.exists(), "Output file was not created."
    with output_file.open() as f:
        file_content = f.read()
        assert "val1" in file_content, "Exported key 'val1' not found in output file."
        assert "abc" in file_content, "Exported value 'abc' not found in output file."
