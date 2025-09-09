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
import time
import traceback
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
        output_path: Path = Path("pulumi_config.json"),  # Default to CWD; previous default escaped project root.
        redactor: Optional[Redactor] = None,
        skip_preview: bool = True,
        atomic: bool = True,
        ensure_resolution: bool = True,
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
        self.ensure_resolution = ensure_resolution
        # Keep a reference to aggregate Output to avoid GC differences across Python versions.
        self._aggregate_output: Optional[pulumi.Output[Any]] = None
        # Enable verbose debug logs by default (can be disabled by setting env var to 0)
        self._debug_enabled = os.getenv("DATAROBOT_PULUMI_EXPORTER_DEBUG", "1") not in {"0", "false", "False"}
        self._log_debug(
            "init",
            output_path=str(self.output_path.resolve()),
            skip_preview=self.skip_preview,
            atomic=self.atomic,
            ensure_resolution=self.ensure_resolution,
        )

    def export(self, name: str, value: Any) -> pulumi.Output[Any]:
        """Register an export to be written later and forward to Pulumi's own export registry."""
        out = pulumi.Output.from_input(value)
        with self._lock:
            self._exports[name] = out
        try:
            pulumi.export(name, out)
            self._log_debug("export-registered", name=name, value_type=str(type(value)))
        except Exception as e:  # pragma: no cover - defensive
            self._log_error(
                "export-failed", name=name, error=str(e), traceback=traceback.format_exc()
            )
            raise
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
        self._log_debug("finalize-called", subset=subset, force=force)
        if self._finalized:
            self._log_debug("finalize-skip-already-finalized")
            return
        try:
            dry_run = pulumi.runtime.is_dry_run()
        except Exception:  # pragma: no cover - defensive
            dry_run = False
            self._log_warn("finalize-dry-run-check-failed", traceback=traceback.format_exc())
        if self.skip_preview and dry_run and not force:
            self._log_info("finalize-skip-preview", dry_run=dry_run, force=force)
            return
        with self._lock:
            total = len(self._exports)
            if not self._exports:
                self._log_info("finalize-no-exports")
                return
            exports = {k: v for k, v in self._exports.items() if subset is None or k in subset}
            if subset is not None:
                self._log_debug(
                    "finalize-subset-filter", subset=subset, before=total, after=len(exports)
                )
            if not exports:
                self._log_info("finalize-no-exports-after-subset")
                self._finalized = True
                return
            aggregate = pulumi.Output.all(**exports)
            # Retain reference on self to avoid GC on some Python versions / runtimes.
            self._aggregate_output = aggregate
        self._log_debug("finalize-aggregate-created", keys=list(exports.keys()))
        try:
            applied = aggregate.apply(lambda resolved: self._write(resolved, on_written))
            if self.ensure_resolution:
                # Export an internal output to ensure dependency graph retains chain.
                pulumi.export("__export_collector_internal__", applied.apply(lambda _: "ok"))
                self._log_debug("finalize-internal-export")
        except Exception as e:  # pragma: no cover
            self._log_error(
                "finalize-apply-failed", error=str(e), traceback=traceback.format_exc()
            )
            raise
        self._finalized = True
        self._log_debug("finalize-scheduled-write")

    # ---- internal ----
    def _apply_redaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.redactor:
            return data
        return {k: self.redactor(k, v) for k, v in data.items()}

    def _write(
        self,
        resolved: Dict[str, Any],
        on_written: Optional[Callable[[Path], None]],
    ) -> None:
        start = time.time()
        self._log_debug(
            "write-start",
            keys=list(resolved.keys()),
            count=len(resolved),
            output_path=str(self.output_path.resolve()),
        )
        data = self._apply_redaction(resolved)
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # pragma: no cover
            self._log_error("write-mkdir-failed", error=str(e), traceback=traceback.format_exc())
            raise
        if self.atomic:
            fd, tmp_name = tempfile.mkstemp(
                prefix="pulumi_exports_", suffix=".json", dir=str(self.output_path.parent)
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, default=str)
                Path(tmp_name).replace(self.output_path)
                self._log_debug("write-atomic-replace", tmp=tmp_name, final=str(self.output_path.resolve()))
            except Exception as e:  # pragma: no cover
                self._log_error(
                    "write-atomic-failed", error=str(e), tmp=tmp_name, traceback=traceback.format_exc()
                )
                try:
                    if Path(tmp_name).exists():
                        Path(tmp_name).unlink()
                finally:
                    raise
        else:
            try:
                with self.output_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, default=str)
                self._log_debug("write-non-atomic-done")
            except Exception as e:  # pragma: no cover
                self._log_error("write-failed", error=str(e), traceback=traceback.format_exc())
                raise
        try:
            size = self.output_path.stat().st_size
        except Exception:  # pragma: no cover
            size = -1
        duration_ms = int((time.time() - start) * 1000)
        self._log_info("write-complete", size=size, ms=duration_ms)
        if on_written:
            try:
                on_written(self.output_path)
            except Exception as e:  # pragma: no cover
                self._log_warn("on_written-callback-error", error=str(e))
        return None  # Pulumi requires a return

    # ---- logging helpers ----
    def _emit(self, level: str, event: str, **fields: Any) -> None:
        if level == "debug" and not self._debug_enabled:
            return
        payload = {"component": "ExportCollector", "event": event, **fields}
        line = json.dumps(payload, default=str)
        try:  # Use pulumi.log if available
            if level == "debug":
                pulumi.log.debug(line)
            elif level == "info":
                pulumi.log.info(line)
            elif level == "warn":
                pulumi.log.warn(line)
            elif level == "error":
                pulumi.log.error(line)
            else:
                pulumi.log.info(line)
        except Exception:  # pragma: no cover - fallback when not in engine context
            print(f"[{level.upper()}] {line}")

    def _log_debug(self, event: str, **fields: Any) -> None:
        self._emit("debug", event, **fields)

    def _log_info(self, event: str, **fields: Any) -> None:
        self._emit("info", event, **fields)

    def _log_warn(self, event: str, **fields: Any) -> None:
        self._emit("warn", event, **fields)

    def _log_error(self, event: str, **fields: Any) -> None:
        self._emit("error", event, **fields)


# Default singleton collector & functional facade
default_collector = ExportCollector()


def export(name: str, value: Any) -> pulumi.Output[Any]:
    return default_collector.export(name, value)


def finalize(**kwargs: Any) -> None:
    default_collector.finalize(**kwargs)
