#!/usr/bin/env python3
"""Load marketplace plugins through a real Codex CLI app-server.

The default command uses the latest published ``@openai/codex`` package. Pass
``--codex-repo`` to build and test a Codex source checkout instead.
"""

from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


class CodexTestError(RuntimeError):
    """A Codex process or protocol error that should fail the compatibility test."""


@dataclass(frozen=True)
class CodexCommand:
    argv: tuple[str, ...]
    description: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "plugins",
        nargs="*",
        metavar="PLUGIN",
        help="marketplace plugin name to load (default: every plugin)",
    )
    parser.add_argument(
        "--marketplace",
        type=Path,
        default=DEFAULT_MARKETPLACE,
        help="path to the Codex marketplace catalog",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--codex-bin",
        type=Path,
        help="use an existing Codex executable instead of the latest published CLI",
    )
    source.add_argument(
        "--codex-repo",
        type=Path,
        help="build and use the Codex checkout at this path",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="with --codex-repo, reuse codex-rs/target/debug/codex without building",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60,
        help="seconds to wait for each app-server response (default: 60)",
    )
    args = parser.parse_args()
    if args.no_build and args.codex_repo is None:
        parser.error("--no-build requires --codex-repo")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def prepare_codex(args: argparse.Namespace) -> CodexCommand:
    if args.codex_bin is not None:
        binary = args.codex_bin.expanduser().resolve()
        if not binary.is_file():
            raise CodexTestError(f"Codex executable does not exist: {binary}")
        return CodexCommand((str(binary),), str(binary))

    if args.codex_repo is None:
        return CodexCommand(
            ("npx", "--yes", "@openai/codex@latest"),
            "latest published @openai/codex",
        )

    codex_repo = args.codex_repo.expanduser().resolve()
    rust_workspace = codex_repo / "codex-rs"
    manifest = rust_workspace / "Cargo.toml"
    if not manifest.is_file():
        raise CodexTestError(f"not a Codex source checkout (missing {manifest})")

    if not args.no_build:
        print(f"Building Codex checkout: {codex_repo}", flush=True)
        result = subprocess.run(
            ["cargo", "build", "--locked", "-p", "codex-cli", "--bin", "codex"],
            cwd=rust_workspace,
            text=True,
        )
        if result.returncode:
            raise CodexTestError(f"Codex build failed with exit code {result.returncode}")

    binary = rust_workspace / "target" / "debug" / ("codex.exe" if sys.platform == "win32" else "codex")
    if not binary.is_file():
        hint = " (remove --no-build to create it)" if args.no_build else ""
        raise CodexTestError(f"Codex executable does not exist: {binary}{hint}")

    revision = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        cwd=codex_repo,
        capture_output=True,
        text=True,
    )
    suffix = revision.stdout.strip() if revision.returncode == 0 else "unknown revision"
    return CodexCommand((str(binary),), f"Codex source checkout {suffix}")


def read_catalog(path: Path, selected: list[str]) -> tuple[Path, list[str]]:
    marketplace = path.expanduser().resolve()
    try:
        catalog = json.loads(marketplace.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise CodexTestError(f"cannot read marketplace {marketplace}: {error}") from error

    entries = catalog.get("plugins")
    if not isinstance(entries, list):
        raise CodexTestError(f"marketplace {marketplace} has no plugins array")
    names = [entry.get("name") for entry in entries if isinstance(entry, dict)]
    if not names or any(not isinstance(name, str) or not name for name in names):
        raise CodexTestError(f"marketplace {marketplace} contains an unnamed plugin")
    if len(names) != len(set(names)):
        raise CodexTestError(f"marketplace {marketplace} contains duplicate plugin names")

    if selected:
        unknown = sorted(set(selected) - set(names))
        if unknown:
            raise CodexTestError(f"plugins not found in marketplace: {', '.join(unknown)}")
        names = list(dict.fromkeys(selected))
    return marketplace, names


class AppServer:
    def __init__(self, command: CodexCommand, cwd: Path, timeout: float):
        self.command = command
        self.cwd = cwd
        self.timeout = timeout
        self.process: subprocess.Popen[str] | None = None
        self.stdout: queue.Queue[str | None] = queue.Queue()
        self.stderr: list[str] = []
        self._next_id = 1

    def __enter__(self) -> AppServer:
        self.process = subprocess.Popen(
            [*self.command.argv, "app-server", "--stdio"],
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._drain_stdout, daemon=True).start()
        threading.Thread(target=self._drain_stderr, daemon=True).start()
        try:
            self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "dot-plugins-compatibility-test",
                        "title": "dot-plugins compatibility test",
                        "version": "1.0.0",
                    },
                    "capabilities": {"experimentalApi": True},
                },
            )
        except Exception:
            self.close()
            raise
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def _drain_stdout(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        for line in self.process.stdout:
            self.stdout.put(line)
        self.stdout.put(None)

    def _drain_stderr(self) -> None:
        assert self.process is not None and self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr.append(line.rstrip())
            if len(self.stderr) > 200:
                del self.stderr[:100]

    def request(self, method: str, params: dict) -> dict:
        assert self.process is not None and self.process.stdin is not None
        request_id = self._next_id
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        try:
            self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise CodexTestError(self._process_failure(f"failed to send {method}: {error}")) from error

        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CodexTestError(self._process_failure(f"timed out waiting for {method}"))
            try:
                line = self.stdout.get(timeout=remaining)
            except queue.Empty as error:
                raise CodexTestError(self._process_failure(f"timed out waiting for {method}")) from error
            if line is None:
                raise CodexTestError(self._process_failure(f"Codex exited while handling {method}"))
            try:
                message = json.loads(line)
            except json.JSONDecodeError as error:
                raise CodexTestError(f"Codex wrote non-JSON output to stdout: {line.rstrip()}") from error
            if message.get("id") != request_id:
                continue
            if "error" in message:
                error = message["error"]
                detail = error.get("message", json.dumps(error)) if isinstance(error, dict) else str(error)
                raise CodexTestError(self._process_failure(f"{method} failed: {detail}"))
            result = message.get("result")
            if not isinstance(result, dict):
                raise CodexTestError(f"{method} returned an invalid result: {message}")
            return result

    def _process_failure(self, message: str) -> str:
        tail = "\n".join(self.stderr[-20:])
        return f"{message}\nCodex stderr:\n{tail}" if tail else message


def codex_version(command: CodexCommand, cwd: Path) -> str:
    try:
        result = subprocess.run(
            [*command.argv, "--version"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CodexTestError(f"could not run {command.description}: {error}") from error
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise CodexTestError(f"could not run {command.description}: {detail}")
    return result.stdout.strip()


def test_plugins(command: CodexCommand, marketplace: Path, names: list[str], timeout: float) -> int:
    version = codex_version(command, REPO_ROOT)
    print(f"Testing with {version} ({command.description})", flush=True)
    print(f"Marketplace: {marketplace}", flush=True)

    failures: list[tuple[str, str]] = []
    with AppServer(command, REPO_ROOT, timeout) as server:
        for name in names:
            try:
                result = server.request(
                    "plugin/read",
                    {
                        "marketplacePath": str(marketplace),
                        "remoteMarketplaceName": None,
                        "pluginName": name,
                    },
                )
                plugin = result.get("plugin")
                summary = plugin.get("summary") if isinstance(plugin, dict) else None
                if not isinstance(summary, dict) or summary.get("name") != name:
                    raise CodexTestError(f"plugin/read returned the wrong plugin summary: {result}")
                if not isinstance(plugin.get("description"), str) or not plugin["description"].strip():
                    raise CodexTestError("plugin/read returned no plugin description")
                interface = summary.get("interface")
                if not isinstance(interface, dict):
                    raise CodexTestError("plugin/read returned no marketplace interface metadata")
                for field in ("displayName", "shortDescription", "longDescription"):
                    if not isinstance(interface.get(field), str) or not interface[field].strip():
                        raise CodexTestError(f"plugin/read returned no interface.{field}")
                for field in ("composerIcon", "logo"):
                    asset = interface.get(field)
                    if not isinstance(asset, str) or not Path(asset).is_file():
                        raise CodexTestError(f"plugin/read returned no usable interface.{field}")
                skills = plugin.get("skills")
                if not isinstance(skills, list) or not skills:
                    raise CodexTestError("plugin/read returned no skills")
                mcp_servers = plugin.get("mcpServers", [])
                hooks = plugin.get("hooks", [])
                print(
                    f"ok  {interface['displayName']}: {len(skills)} skills, "
                    f"{len(mcp_servers)} MCP servers, {len(hooks)} hooks"
                )
            except CodexTestError as error:
                failures.append((name, str(error)))
                print(f"FAIL {name}", file=sys.stderr)

    if failures:
        print("\nCodex compatibility failures:", file=sys.stderr)
        for name, detail in failures:
            print(f"\n[{name}]\n{detail}", file=sys.stderr)
        return 1
    print(f"Loaded {len(names)} plugin(s) successfully.")
    return 0


def main() -> int:
    args = parse_args()
    try:
        marketplace, names = read_catalog(args.marketplace, args.plugins)
        command = prepare_codex(args)
        return test_plugins(command, marketplace, names, args.timeout)
    except (CodexTestError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
