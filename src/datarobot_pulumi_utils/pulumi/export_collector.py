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
        output_path: Path = Path("../pulumi_config.json"),
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
        # Incremental resolution tracking
        self._resolved_values: Dict[str, Any] = {}
        self._pending: set[str] = set()
        self._finalize_invoked = False
        self._final_file_written = False
        self._subset_filter: Optional[set[str]] = None
        self._last_write_time: float = 0.0
        self._min_write_interval_sec: float = float(os.getenv("DATAROBOT_PULUMI_EXPORTER_MIN_INTERVAL", "0.2"))
        self._incremental_enabled = os.getenv("DATAROBOT_PULUMI_EXPORTER_INCREMENTAL", "1") not in {"0","false","False"}
        # Enable verbose debug logs by default (can be disabled by setting env var to 0)
        self._debug_enabled = os.getenv("DATAROBOT_PULUMI_EXPORTER_DEBUG", "1") not in {"0", "false", "False"}
        self._log_debug(
            "init",
            output_path=str(self.output_path.resolve()),
            skip_preview=self.skip_preview,
            atomic=self.atomic,
            ensure_resolution=self.ensure_resolution,
        )

    # (Removed dynamic provider approach in favor of simpler per-output taps.)

    def export(self, name: str, value: Any) -> pulumi.Output[Any]:
        """Register an export to be written later and forward to Pulumi's own export registry."""
        out = pulumi.Output.from_input(value)
        with self._lock:
            self._exports[name] = out
            self._pending.add(name)
        try:
            pulumi.export(name, out)
            self._log_debug("export-registered", name=name, value_type=str(type(value)))
        except Exception as e:  # pragma: no cover - defensive
            self._log_error(
                "export-failed", name=name, error=str(e), traceback=traceback.format_exc()
            )
            raise
        # Per-output tap: when this resolves, record its value & maybe write snapshot.
        def _capture(val: Any, key=name):  # capture key in default
            with self._lock:
                self._resolved_values[key] = val
                self._log_debug(
                    "value-resolved", name=key, has_value=val is not None, type=str(type(val))
                )
                if key in self._pending:
                    self._pending.remove(key)
                self._maybe_write_snapshot(reason="incremental" if self._incremental_enabled else "capture", force=self._incremental_enabled)
                self._maybe_finalize_if_complete()
            return val
        # Keep reference to tap output to avoid GC discarding the apply.
        _ = out.apply(_capture)
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
        except Exception:  # pragma: no cover
            dry_run = False
            self._log_warn("finalize-dry-run-check-failed", traceback=traceback.format_exc())
        if self.skip_preview and dry_run and not force:
            self._log_info("finalize-skip-preview", dry_run=dry_run, force=force)
            return
        with self._lock:
            if not self._exports:
                self._log_info("finalize-no-exports")
                return
            self._finalize_invoked = True
            self._subset_filter = set(subset) if subset else None
            total = len(self._exports)
            resolved = len(self._resolved_values)
            self._log_debug(
                "finalize-progress", total=total, resolved=resolved, pending=list(self._pending)
            )
            # Attempt immediate snapshot if any resolved.
            if resolved:
                self._maybe_write_snapshot(reason="finalize")
            # If all already resolved, mark done.
            self._maybe_finalize_if_complete()
        self._finalized = True

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

    # Snapshot writing from incremental taps/finalize
    def _maybe_write_snapshot(self, reason: str, force: bool = False) -> None:
        if self._final_file_written and not force:
            return
        now = time.time()
        if not force and (now - self._last_write_time) < self._min_write_interval_sec:
            return
        data = dict(self._resolved_values)
        if self._subset_filter is not None:
            data = {k: v for k, v in data.items() if k in self._subset_filter}
        if not data:
            return
        self._last_write_time = now
        self._log_debug(
            "snapshot-attempt", keys=list(data.keys()), reason=reason, complete=len(self._pending)==0
        )
        try:
            self._write(data, on_written=None)
        except Exception as e:  # pragma: no cover
            self._log_warn("snapshot-write-error", error=str(e))

    def _maybe_finalize_if_complete(self) -> None:
        if not self._finalize_invoked:
            return
        if self._pending:
            return
        if self._final_file_written:
            return
        # All resolved: final snapshot write (force) + mark
        self._log_info("all-resolved")
        self._maybe_write_snapshot(reason="all-resolved", force=True)
        self._final_file_written = True

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
