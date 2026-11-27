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
"""Write a Pulumi program's outputs into a .env file or a DataRobot workload manifest.

Call these from the program, next to ``pulumi.export``::

    outputs = {"DATAROBOT_USE_CASE_ID": use_case.id, "MEMORY_SPACE_ID": space.id}
    for name, value in outputs.items():
        pulumi.export(name, value)
    write_dotenv("../.env", outputs)  # or write_manifest("../.datarobot.yaml", outputs)

The file is written once, after ``pulumi up`` has resolved every output; ``pulumi preview``
writes nothing. If a resource fails, its output never resolves and the file is left as it was.
Secret outputs are left out with a warning: export a credential id instead.

``write_dotenv`` replaces an existing ``NAME=`` line in place (``export NAME=...`` keeps its
``export``) or appends one. Nothing else in the file changes.

``write_manifest`` sets the top-level ``useCaseId`` from ``DATAROBOT_USE_CASE_ID``. Every other
output becomes a ``source: string`` entry of the workload's ``environmentVars``, between the
``# >>> infra outputs`` and ``# <<< infra outputs`` markers. The whole block is rewritten each
time, so removing an output removes its variable. A missing marker or a name also declared
outside the block fails the update.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

import pulumi

START_MARKER = "# >>> infra outputs"
END_MARKER = "# <<< infra outputs"
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
# A `name:` line of an environmentVars entry, uncommented (`- name: X` or `  name: X`).
NAME_LINE = re.compile(r"^\s*(?:-\s+)?name:\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*$")
VALUE_LINE = re.compile(r"^\s*value:\s*(.*?)\s*$")
USE_CASE_OUTPUT = "DATAROBOT_USE_CASE_ID"
USE_CASE_LINE = re.compile(r"^useCaseId:.*$")


class ManifestError(Exception):
    """The manifest can't be updated safely (missing markers, a name clash)."""


def write_dotenv(path: str | Path, outputs: Mapping[str, pulumi.Input[Any]]) -> pulumi.Output[None] | None:
    """Write ``outputs`` into the .env file at ``path`` once they resolve. See the module docstring."""
    return _when_resolved(outputs, lambda env: _write_dotenv(Path(path), env))


def write_manifest(path: str | Path, outputs: Mapping[str, pulumi.Input[Any]]) -> pulumi.Output[None] | None:
    """Write ``outputs`` into the manifest at ``path`` once they resolve. See the module docstring."""
    return _when_resolved(outputs, lambda env: _write_manifest(Path(path), env))


def _when_resolved(
    outputs: Mapping[str, pulumi.Input[Any]], write: Callable[[dict[str, str]], None]
) -> pulumi.Output[None] | None:
    """Call ``write`` with the scalar, non-secret ``outputs`` as strings, once all of them resolve.

    Returns the Output of that call (None in preview), so a caller or a test can wait for the write.
    """
    bad = [name for name in outputs if not ENV_NAME.match(name)]
    if bad:
        raise ValueError(f"not environment variable names: {', '.join(bad)}")
    if pulumi.runtime.is_dry_run():
        return None
    resolved = {name: pulumi.Output.from_input(value) for name, value in outputs.items()}
    secret: dict[str, pulumi.Output[bool]] = {
        name: pulumi.Output.from_input(output.is_secret()) for name, output in resolved.items()
    }

    def _write(args: list[Any]) -> None:
        # `Output.all()` with no outputs resolves to [], not {}.
        values, is_secret = dict(args[0]), dict(args[1])
        env: dict[str, str] = {}
        for name, value in sorted(values.items()):
            if is_secret[name]:
                pulumi.log.warn(
                    f"skipped {name}: it is a secret. Store it as a DataRobot credential and export its id."
                )
            elif isinstance(value, bool):
                env[name] = "true" if value else "false"
            elif isinstance(value, (str, int, float)):
                env[name] = str(value)
            else:
                pulumi.log.warn(f"skipped {name}: only string, number and bool outputs are written")
        write(env)

    return pulumi.Output.all(pulumi.Output.all(**resolved), pulumi.Output.all(**secret)).apply(_write)


def _write_dotenv(path: Path, env: dict[str, str]) -> None:
    text = path.read_text() if path.exists() else ""
    new_text = set_dotenv(text, env)
    if new_text != text:
        path.write_text(new_text)
        pulumi.log.info(f"wrote {', '.join(env)} to {path}")


def _write_manifest(path: Path, env: dict[str, str]) -> None:
    use_case_id = env.pop(USE_CASE_OUTPUT, None)
    text = path.read_text()
    new_text, previous = update_manifest(text, env)
    changes = describe_changes(previous, env)
    if use_case_id:
        new_text = set_use_case(new_text, use_case_id)
        if f"useCaseId: {use_case_id}\n" not in text:
            changes.append(f"  ~ useCaseId: {use_case_id}")
    if new_text != text:
        path.write_text(new_text)
        pulumi.log.info("\n".join([f"updated {path}:", *changes]))


def _assignment(name: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=")


def set_dotenv(text: str, values: Mapping[str, str]) -> str:
    """``text`` with each ``NAME=value`` of ``values`` replaced in place, or appended."""
    lines = text.splitlines(keepends=True)
    for name, value in values.items():
        line = f"{name}={value}\n"
        matches = [i for i, existing in enumerate(lines) if _assignment(name).match(existing)]
        if matches:
            # Keep an `export ` prefix, for a .env that is sourced in a shell.
            exported = lines[matches[0]].lstrip().startswith("export")
            lines[matches[0]] = f"export {line}" if exported else line
            # A later duplicate would win when .env is loaded: drop it.
            for i in reversed(matches[1:]):
                del lines[i]
        else:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(line)
    return "".join(lines)


def _find_block(lines: list[str]) -> tuple[int, int, str]:
    starts = [i for i, line in enumerate(lines) if line.strip().startswith(START_MARKER)]
    ends = [i for i, line in enumerate(lines) if line.strip().startswith(END_MARKER)]
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ManifestError(
            f"expected one '{START_MARKER}' line followed by one '{END_MARKER}' line in environmentVars"
        )
    start = starts[0]
    # Entries line up with the list item before the block; a formatter may have moved the comments.
    item = next((line for line in reversed(lines[:start]) if line.lstrip().startswith("- ")), lines[start])
    indent = item[: len(item) - len(item.lstrip())]
    return start, ends[0], indent


def _parse_block(block: list[str]) -> dict[str, str]:
    entries: dict[str, str] = {}
    name: str | None = None
    for line in block:
        if line.lstrip().startswith("#"):
            continue
        if m := NAME_LINE.match(line):
            name = m.group(1)
            entries[name] = ""
        elif name and (m := VALUE_LINE.match(line)):
            raw = m.group(1)
            try:
                entries[name] = json.loads(raw) if raw.startswith('"') else raw.strip("'")
            except json.JSONDecodeError:
                entries[name] = raw
    return entries


def _render_block(env: Mapping[str, str], indent: str) -> list[str]:
    out: list[str] = []
    for name in sorted(env):
        out += [
            f"{indent}- source: string\n",
            f"{indent}  name: {name}\n",
            # A JSON string is a valid YAML double-quoted scalar.
            f"{indent}  value: {json.dumps(env[name])}\n",
        ]
    return out


def update_manifest(text: str, env: Mapping[str, str]) -> tuple[str, dict[str, str]]:
    """Rewrite the marked block for ``env``. Return (new text, the block's previous entries)."""
    lines = text.splitlines(keepends=True)
    start, end, indent = _find_block(lines)
    previous = _parse_block(lines[start + 1 : end])
    outside = {
        m.group(1)
        for i, line in enumerate(lines)
        if not (start <= i <= end) and not line.lstrip().startswith("#") and (m := NAME_LINE.match(line))
    }
    clashes = sorted(outside & set(env))
    if clashes:
        raise ManifestError(
            f"{', '.join(clashes)} declared both by the stack and outside the infra outputs block; remove one of them"
        )
    new_lines = lines[: start + 1] + _render_block(env, indent) + lines[end:]
    return "".join(new_lines), previous


def set_use_case(text: str, use_case_id: str) -> str:
    """``text`` with the top-level ``useCaseId`` set: replaced in place, or added after ``name``."""
    lines = text.splitlines(keepends=True)
    line = f"useCaseId: {use_case_id}\n"
    for i, existing in enumerate(lines):
        if USE_CASE_LINE.match(existing):
            lines[i] = line
            return "".join(lines)
    after_name = next((i + 1 for i, existing in enumerate(lines) if existing.startswith("name:")), 0)
    lines.insert(after_name, line)
    return "".join(lines)


def describe_changes(previous: Mapping[str, str], current: Mapping[str, str]) -> list[str]:
    report = []
    for name in sorted(set(previous) | set(current)):
        if name not in previous:
            report.append(f"  + {name}={current[name]}")
        elif name not in current:
            report.append(f"  - {name}")
        elif previous[name] != current[name]:
            report.append(f"  ~ {name}={current[name]} (was {previous[name]})")
    return report
