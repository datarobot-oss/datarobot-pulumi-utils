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
"""
Public interface for pulumi-exporter.

Typical use:

    from pulumi_exporter import export, finalize

    bucket = aws.s3.Bucket("b")
    export("bucket_name", bucket.id)
    finalize()  # writes pulumi_exports.json by default (after resolution)

Or with a custom path & redactor:

    from pulumi_exporter import ExportCollector

    collector = ExportCollector(output_path="build/stack_outputs.json",
                                redactor=lambda k,v: "***" if "secret" in k else v)
    export = collector.export  # optional alias
    # define resources ...
    collector.finalize()

To patch existing code using pulumi.export:

    from pulumi_exporter import patch_pulumi_export
    patch_pulumi_export()
    # existing pulumi.export(...) calls are now captured
    finalize()
"""

__all__ = [
    "ExportCollector",
    "default_collector",
    "export",
    "finalize",
]


import json
import os
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, Optional

import pulumi

Redactor = Callable[[str, Any], Any]


class ExportCollector:
    """
    Collects Pulumi stack exports and writes them once after all resolve.

    Features:
    - Aggregates all exported Outputs.
    - Skips writing during preview (unless force=True).
    - Atomic file write (temp file + replace).
    - Optional redaction of sensitive values.
    - Optional filtering subset on finalize.

    Thread-safety: export() is lock-protected.
    """

    def __init__(
        self,
        output_path: Path = Path("../pulumi_config.json"),
        redactor: Optional[Redactor] = None,
        skip_preview: bool = True,
        atomic: bool = True,
    ):
        """
        :param output_path: Path to write final exports JSON.
        :param redactor: Optional function to redact sensitive values.
                         Should accept (key, value) and return redacted value.
        :param skip_preview: Skip writing during Pulumi preview phase.
        :param atomic: Use atomic file write (temp file + replace).
        """
        self._exports: Dict[str, pulumi.Output[Any]] = {}
        self._lock = Lock()
        self.output_path = Path(output_path)
        self.redactor = redactor
        self.skip_preview = skip_preview
        self.atomic = atomic
        self._finalized = False
        # Track resolved values for incremental writing
        self._resolved_values: Dict[str, Any] = {}
        self._finalize_invoked = False

    def export(self, name: str, value: Any) -> pulumi.Output[Any]:
        """
        Register an export to be written later.
        Returns the Output for chaining.
        """
        out = pulumi.Output.from_input(value)
        with self._lock:
            self._exports[name] = out
        pulumi.export(name, out)

        # Capture resolved values incrementally
        def _capture(val: Any) -> Any:
            with self._lock:
                self._resolved_values[name] = val
                # Write snapshot if finalize has been called and we have values
                if self._finalize_invoked and self._resolved_values:
                    self._write_current_values()
            return val

        out.apply(_capture)
        return out

    def finalize(
        self,
        subset: Optional[list[str]] = None,
        force: bool = False,
        on_written: Optional[Callable[[Path], None]] = None,
    ) -> None:
        """
        Resolve all collected outputs and write them to the output_path.
        subset: only write these keys (others still exported to Pulumi).
        force: write even during preview.
        on_written: callback invoked with final path after write.
        """
        if self._finalized:
            return
        if self.skip_preview and pulumi.runtime.is_dry_run() and not force:
            return
        with self._lock:
            if not self._exports:
                return
            self._finalize_invoked = True
            self._subset_filter = set(subset) if subset else None
            # Write any values we already have
            if self._resolved_values:
                self._write_current_values(on_written)
        self._finalized = True

    def _apply_redaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.redactor:
            return data
        return {k: self.redactor(k, v) for k, v in data.items()}

    def _write_current_values(self, on_written: Optional[Callable[[Path], None]] = None) -> None:
        """Write currently resolved values to file."""
        data = dict(self._resolved_values)
        if hasattr(self, "_subset_filter") and self._subset_filter is not None:
            data = {k: v for k, v in data.items() if k in self._subset_filter}
        if not data:
            return
        self._write(data, on_written)

    def _write(
        self,
        resolved: Dict[str, Any],
        on_written: Optional[Callable[[Path], None]],
    ) -> None:
        data = self._apply_redaction(resolved)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        if self.atomic:
            # Note, there are edge cases where this might not actually be atomic despite the `self.atomic` flag.
            # If we see issues like this in the wild, take a look at:
            #  https://python-atomicwrites.readthedocs.io/en/latest/_modules/atomicwrites.html#atomic_write
            fd, tmp_name = tempfile.mkstemp(prefix="pulumi_exports_", suffix=".json", dir=str(self.output_path.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, default=str)
                Path(tmp_name).replace(self.output_path)
            except Exception:
                # Best effort cleanup; ignore secondary errors.
                try:
                    if Path(tmp_name).exists():
                        Path(tmp_name).unlink()
                finally:
                    raise
        else:
            with self.output_path.open("w") as f:
                json.dump(data, f, indent=4, default=str)
        if on_written:
            on_written(self.output_path)
        return None  # Pulumi requires a return


# Default singleton collector & functional facade
default_collector = ExportCollector()


def export(name: str, value: Any) -> pulumi.Output[Any]:
    return default_collector.export(name, value)


def finalize(**kwargs: Any) -> None:
    default_collector.finalize(**kwargs)
