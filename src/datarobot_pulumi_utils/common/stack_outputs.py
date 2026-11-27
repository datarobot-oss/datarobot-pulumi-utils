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
"""Write a Pulumi stack's outputs into a .env file or a DataRobot workload manifest.

``pulumi-outputs dotenv NAME...`` writes the named outputs into ``.env``. An existing ``NAME=``
line is replaced in place (``export NAME=...`` keeps its ``export``); otherwise the line is
appended. Nothing else in the file changes.

``pulumi-outputs manifest`` writes into ``.datarobot.yaml``. ``DATAROBOT_USE_CASE_ID`` becomes
the top-level ``useCaseId``. Every other output whose name looks like an environment variable
(``^[A-Z][A-Z0-9_]*$``) and whose value is a scalar becomes a ``source: string`` entry of the
workload's ``environmentVars``, between the ``# >>> infra outputs`` and ``# <<< infra outputs``
markers. The whole block is rewritten each run, so removing an export removes its variable.
Secret outputs are skipped: export a credential id instead.

Both run ``pulumi stack output --json`` once, in the current directory.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROG = "pulumi-outputs"
START_MARKER = "# >>> infra outputs"
END_MARKER = "# <<< infra outputs"
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
# A `name:` line of an environmentVars entry, uncommented (`- name: X` or `  name: X`).
NAME_LINE = re.compile(r"^\s*(?:-\s+)?name:\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*$")
VALUE_LINE = re.compile(r"^\s*value:\s*(.*?)\s*$")
SECRET = "[secret]"
# Pulumi's placeholder for an output it couldn't compute: what `pulumi stack output` shows for a
# resource an update didn't reach (a failed or `--target` update).
UNKNOWN = "04da6b54-80e4-46f7-96ec-b56ff0331ba9"
USE_CASE_OUTPUT = "DATAROBOT_USE_CASE_ID"
USE_CASE_LINE = re.compile(r"^useCaseId:.*$")


class ManifestError(Exception):
    """The manifest can't be updated safely (missing markers, a name clash)."""


def read_stack_outputs(stack: str) -> dict[str, object] | None:
    """`pulumi stack output --json` of ``stack``, or None (with a message) when it can't be read."""
    if shutil.which("pulumi") is None:
        print(f"{PROG}: pulumi is not on PATH.", file=sys.stderr)
        return None
    result = subprocess.run(
        ["pulumi", "stack", "output", "--json", "--non-interactive", "--stack", stack],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        print(f"{PROG}: no outputs from Pulumi stack {stack}.", file=sys.stderr)
        return None
    outputs: dict[str, object] = json.loads(result.stdout or "{}")
    return outputs


def _assignment(name: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=")


def set_dotenv(text: str, values: dict[str, str]) -> str:
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


def select_dotenv_outputs(outputs: dict[str, object], names: list[str]) -> dict[str, str]:
    """The non-empty string outputs among ``names``, in that order."""
    return {name: value for name in names if isinstance(value := outputs.get(name), str) and value and value != UNKNOWN}


def select_manifest_outputs(outputs: dict[str, object], stack: str) -> tuple[dict[str, str], list[str]]:
    """Return (env vars to write, warnings) from `pulumi stack output --json`."""
    env: dict[str, str] = {}
    warnings: list[str] = []
    for name, value in sorted(outputs.items()):
        if not ENV_NAME.match(name):
            continue
        if value == SECRET:
            warnings.append(
                f"skipped {name}: it is a secret output, and the manifest stores literals. "
                "Store the secret as a DataRobot credential and export its id instead."
            )
        elif value == UNKNOWN:
            warnings.append(
                f"skipped {name}: its resource hasn't been created yet; run `pulumi up` on stack {stack} to create it"
            )
        elif value is None:
            warnings.append(f"skipped {name}: its value is null")
        elif isinstance(value, bool):
            env[name] = "true" if value else "false"
        elif isinstance(value, (str, int, float)):
            env[name] = str(value)
        else:
            warnings.append(f"skipped {name}: only scalar outputs become env vars")
    return env, warnings


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


def _render_block(env: dict[str, str], indent: str) -> list[str]:
    out: list[str] = []
    for name in sorted(env):
        out += [
            f"{indent}- source: string\n",
            f"{indent}  name: {name}\n",
            # A JSON string is a valid YAML double-quoted scalar.
            f"{indent}  value: {json.dumps(env[name])}\n",
        ]
    return out


def update_manifest(text: str, env: dict[str, str]) -> tuple[str, dict[str, str], dict[str, str]]:
    """Rewrite the marked block for `env`. Return (new text, previous entries, new entries)."""
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
    return "".join(new_lines), previous, env


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


def describe_changes(previous: dict[str, str], current: dict[str, str]) -> list[str]:
    report = []
    for name in sorted(set(previous) | set(current)):
        if name not in previous:
            report.append(f"  + {name}={current[name]}")
        elif name not in current:
            report.append(f"  - {name}")
        elif previous[name] != current[name]:
            report.append(f"  ~ {name}={current[name]} (was {previous[name]})")
    return report


def write_dotenv(outputs: dict[str, object], path: Path, names: list[str], optional: list[str]) -> int:
    values = select_dotenv_outputs(outputs, names + optional)
    missing = [name for name in names if name not in values]
    if missing:
        print(f"{PROG}: the stack has no {', '.join(missing)} output; {path.name} unchanged.", file=sys.stderr)
        return 1
    text = path.read_text() if path.exists() else ""
    new_text = set_dotenv(text, values)
    if new_text != text:
        path.write_text(new_text)
    for name, value in values.items():
        print(f"{PROG}: {name}={value} in {path.name}")
    return 0


def write_manifest(outputs: dict[str, object], path: Path, stack: str) -> int:
    env, warnings = select_manifest_outputs(outputs, stack)
    for warning in warnings:
        print(f"{PROG}: {warning}", file=sys.stderr)
    use_case_id = env.pop(USE_CASE_OUTPUT, None)

    text = path.read_text()
    try:
        new_text, previous, current = update_manifest(text, env)
    except ManifestError as exc:
        print(f"{PROG}: {exc}", file=sys.stderr)
        return 1

    changes = describe_changes(previous, current)
    if use_case_id:
        new_text = set_use_case(new_text, use_case_id)
        if f"useCaseId: {use_case_id}\n" not in text:
            changes.append(f"  ~ useCaseId: {use_case_id}")
    if new_text != text:
        path.write_text(new_text)
    if changes:
        print(f"{PROG}: updated {path.name}:")
        print("\n".join(changes))
    else:
        print(f"{PROG}: {path.name} is up to date ({len(current)} vars).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROG, description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--stack", required=True)
    parser.add_argument(
        "--outputs-json",
        type=Path,
        help="read outputs from this file instead of running `pulumi stack output --json`",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    dotenv = commands.add_parser("dotenv", help="write the named outputs into a .env file")
    dotenv.add_argument("names", nargs="+", metavar="NAME", help="an output that must exist")
    dotenv.add_argument("--optional", action="append", default=[], metavar="NAME", help="written when present")
    dotenv.add_argument("--file", type=Path, default=Path(".env"))

    manifest = commands.add_parser("manifest", help="write env-shaped outputs into a workload manifest")
    manifest.add_argument("--file", type=Path, default=Path(".datarobot.yaml"))
    manifest.add_argument(
        "--allow-missing-stack",
        action="store_true",
        help="exit 0 and leave the file alone when the stack can't be read",
    )
    args = parser.parse_args(argv)

    outputs = json.loads(args.outputs_json.read_text()) if args.outputs_json else read_stack_outputs(args.stack)
    if outputs is None:
        if getattr(args, "allow_missing_stack", False):
            print(f"{PROG}: leaving {args.file.name} as it is.")
            return 0
        return 1
    if args.command == "dotenv":
        return write_dotenv(outputs, args.file, args.names, args.optional)
    return write_manifest(outputs, args.file, args.stack)


if __name__ == "__main__":
    sys.exit(main())
