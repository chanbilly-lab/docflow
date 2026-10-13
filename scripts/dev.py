"""Cross-platform local developer commands. Run from any working directory."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"
PYTHON = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True)


def frontend_env() -> dict[str, str]:
    env = os.environ.copy()
    # An optional project-local runtime avoids replacing an existing system Node.
    local_nodes = sorted((ROOT / ".tools").glob("node-v22.*-win-x64/node.exe"))
    if os.name == "nt" and local_nodes:
        env["PATH"] = str(local_nodes[-1].parent) + os.pathsep + env.get("PATH", "")
    node = shutil.which("node", path=env.get("PATH"))
    if not node:
        raise RuntimeError("Install Node 22.12+ (22.x) and put it on PATH.")
    version = subprocess.check_output([node, "--version"], text=True).strip()
    parts = tuple(int(part) for part in version.lstrip("v").split("."))
    if parts[0] != 22 or parts < (22, 12, 0):
        raise RuntimeError(f"Node 22.12+ (22.x) required; found {version}.")
    return env


def npm(*args: str) -> None:
    env = frontend_env()
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm", path=env.get("PATH"))
    if not executable:
        raise RuntimeError("npm is missing; install the Node distribution with npm.")
    run([executable, *args], FRONTEND, env)


def backend(*args: str, cwd: Path = BACKEND) -> None:
    if not PYTHON.exists():
        raise RuntimeError("Run bootstrap first to create backend/.venv.")
    run([str(PYTHON), *args], cwd)


def bootstrap() -> None:
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("Bootstrap requires Python 3.13; on Windows use py -3.13.")
    frontend_env()
    if not PYTHON.exists():
        venv.EnvBuilder(with_pip=True).create(VENV)
    backend("-m", "pip", "install", "-r", "requirements-dev.txt")
    backend("-m", "pip", "install", "--no-build-isolation", "--no-deps", "-e", ".")
    npm("ci")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "bootstrap",
            "check",
            "format",
            "dev",
            "backend-test",
            "backend-lint",
            "backend-typecheck",
            "backend-build",
            "frontend-test",
            "frontend-lint",
            "frontend-typecheck",
            "frontend-build",
        ],
    )
    command = parser.parse_args().command
    if command == "bootstrap":
        bootstrap()
    elif command == "check":
        backend("-m", "ruff", "check", ".", "../scripts")
        backend("-m", "ruff", "format", "--check", ".", "../scripts")
        backend("-m", "mypy")
        backend("-m", "mypy", "--strict", "../scripts")
        backend("-m", "pytest")
        for script in ["format:check", "lint", "test", "build"]:
            npm("run", script)
        backend("-m", "build", "--no-isolation")
    elif command == "format":
        backend("-m", "ruff", "format", ".", "../scripts")
        npm("run", "format")
    elif command == "dev":
        npm("run", "dev")
    elif command == "backend-test":
        backend("-m", "pytest")
    elif command == "backend-lint":
        backend("-m", "ruff", "check", ".", "../scripts")
    elif command == "backend-typecheck":
        backend("-m", "mypy")
        backend("-m", "mypy", "--strict", "../scripts")
    elif command == "backend-build":
        backend("-m", "build", "--no-isolation")
    else:
        npm("run", command.removeprefix("frontend-"))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
