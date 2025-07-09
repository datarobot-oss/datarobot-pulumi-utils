import os
import pathlib
import sys
from typing import Any, Dict, Optional

import papermill as pm
import pulumi
import yaml
from pulumi import Input, Output, dynamic


class PapermillProvider(dynamic.ResourceProvider):
    """
    Custom Pulumi resource provider for executing notebooks with Papermill
    """

    def diff(self, _id: str, _olds: Dict[str, Any], _news: Dict[str, Any]) -> dynamic.DiffResult:
        """
        Diff checks what impacts a hypothetical update will have on the resource's properties.
        """
        # For this resource, we always want to re-execute the notebook if any properties change
        if (
            _olds["input_path"] != _news["input_path"]
            or _olds.get("parameters") != _news.get("parameters")
            or not os.path.exists(_news.get("result_file", ""))
        ):
            return dynamic.DiffResult(changes=True)
        else:
            # No changes needed, return no changes
            return dynamic.DiffResult(changes=False)

    def create(self, props: Dict[str, Any]) -> dynamic.CreateResult:
        """Execute notebook during resource creation"""
        return self._execute_notebook(props)

    def update(self, id: str, _olds: Dict[str, Any], _news: Dict[str, Any]) -> dynamic.UpdateResult:
        """Execute notebook during resource update"""
        result = self._execute_notebook(_news)
        return dynamic.UpdateResult(outs=result.outs)

    def delete(self, _id: str, _props: Dict[str, Any]) -> None:
        """Cleanup during resource deletion (optional)"""
        output_path = _props.get("output_path")
        input_path = _props.get("input_path")
        if output_path and os.path.exists(output_path) and output_path != input_path:
            try:
                os.remove(output_path)
                pulumi.log.info(f"Cleaned up output file: {output_path}")
            except Exception as e:
                pulumi.log.warn(f"Warning: Could not clean up output file {output_path}: {e}")

        result_file = _props.get("result_file", None)
        if result_file and os.path.exists(result_file):
            try:
                os.remove(result_file)
                pulumi.log.info(f"Cleaned up result file: {result_file}")
            except Exception as e:
                pulumi.log.warn(f"Warning: Could not clean up result file {result_file}: {e}")

    def _execute_notebook(self, props: Dict[str, Any]) -> dynamic.CreateResult:
        """Execute the notebook with Papermill"""
        input_path = pathlib.Path(props["input_path"])
        output_path = pathlib.Path(props["output_path"]) if "output_path" in props else None
        parameters = props.get("parameters", {})
        result_file = props.get("result_file", {})
        cwd = input_path.parent

        # Validate input file exists
        if not os.path.exists(input_path):
            raise Exception(f"Input notebook not found: {input_path}")

        for key, value in parameters.items():
            os.environ[key] = str(value)

        try:
            # Execute notebook with Papermill
            pulumi.log.info(f"Executing notebook: {input_path}")
            pulumi.log.info(f"Parameters: {parameters}")

            pm.execute_notebook(
                input_path=input_path,
                output_path=output_path,
                cwd=cwd,
                log_output=False,
                progress_bar=False,
                stderr_file=sys.stderr,
                stdout_file=sys.stdout,
            )

            pulumi.log.info(f"Notebook executed successfully: {input_path}")

            result_from_file: Dict[str, Any] = {}

            if not os.path.exists(result_file):
                with open(result_file, "w") as f:
                    yaml.dump(result_from_file, f)
            else:
                with open(result_file) as f:
                    result_from_file = yaml.safe_load(f)

            return dynamic.CreateResult(
                id_=f"papermill-{hash(props['input_path'] + str(parameters))}",
                outs={
                    "input_path": props["input_path"],
                    "output_path": props.get("output_path", None),
                    "parameters": props.get("parameters", {}),
                    "result": result_from_file,
                    "result_file": str(result_file),
                    "cwd": props.get("cwd", os.getcwd()),
                },
            )

        except Exception as e:
            pulumi.log.error(f"Error executing notebook {input_path}: {str(e)}")
            raise Exception(f"Notebook execution failed: {str(e)}")


class PapermillResource(dynamic.Resource):
    """
    Custom Pulumi resource for executing Jupyter notebooks with Papermill
    """

    result: Output[Dict[str, Any]]

    def __init__(
        self,
        name: str,
        input_path: str,
        output_path: Optional[str] = None,
        parameters: Optional[Input[Dict[str, Any]]] = None,
        result_file: Optional[str] = None,
        cwd: Optional[str] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ):
        """
        :param str name: The resource name
        :param str input_path: Path to the input notebook
        :param Optional[str] output_path: Path where the executed notebook will be saved
        :param Optional[Input[Dict[str, Any]]] parameters: Dictionary of parameters to pass to the notebook
        :param Optional[str] result_file: Path to read the result from the executed notebook, by default it will be created in the same directory as the input notebook with _output.yaml suffix
        :param Optional[str] cwd: Working directory for notebook execution, defaults to the directory of the input notebook
        :param Optional[pulumi.ResourceOptions] opts: Standard Pulumi resource options
        :raises Exception: If the input notebook does not exist
        :raises Exception: If the result file cannot be created or read
        """

        # Set defaults
        if parameters is None:
            parameters = {}
        if result_file is None:
            _input_path = pathlib.Path(input_path)
            # create result file path by adding _output.yaml to the end of the input notebook name
            result_file = str(_input_path.parent / f"{_input_path.name}_output.yaml")
        if cwd is None:
            cwd = os.getcwd()

        # Create the resource
        super().__init__(
            PapermillProvider(),
            name,
            {
                "input_path": input_path,
                "output_path": output_path,
                "parameters": parameters,
                "result": {},
                "result_file": result_file,
                "cwd": cwd,
            },
            opts,
        )
