#!/usr/bin/env python3
"""Run a command with a timeout while capturing stdout and stderr."""

from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path


TIMEOUT_EXIT_CODE = 124


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--stdout", required=True)
    parser.add_argument("--stderr", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("command is required after --")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be greater than zero")
    return args


def terminate_process(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        proc.terminate()

    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except OSError:
            proc.kill()
        proc.wait()


def main() -> int:
    args = parse_args()
    stdout_path = Path(args.stdout)
    stderr_path = Path(args.stderr)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)

    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        proc = subprocess.Popen(
            args.command,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
        )
        try:
            return proc.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            terminate_process(proc)

    with stderr_path.open("ab") as stderr_file:
        stderr_file.write(
            f"\n[timeout] command exceeded {args.timeout_seconds:g}s: "
            f"{' '.join(args.command)}\n".encode("utf-8", errors="replace")
        )
    return TIMEOUT_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
