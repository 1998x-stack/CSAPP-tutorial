#!/usr/bin/env python3
"""Compare deterministic stdout (or expected stderr) from a compiled C lab."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--exit-code", default=0, type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.command
    if cmd[:1] == ["--"]:
        cmd = cmd[1:]
    if not cmd:
        parser.error("missing command following --")
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
    except subprocess.TimeoutExpired:
        print("test process timed out", file=sys.stderr)
        return 1
    expected = args.expected.read_text(encoding="utf-8").replace("\r\n", "\n")
    observed = run.stdout if args.exit_code == 0 else run.stderr
    if run.returncode != args.exit_code or observed != expected:
        print(f"command: {cmd}", file=sys.stderr)
        print(f"expected exit: {args.exit_code}, got: {run.returncode}", file=sys.stderr)
        print(f"expected output: {expected!r}", file=sys.stderr)
        print(f"actual output:   {observed!r}", file=sys.stderr)
        print(f"stderr: {run.stderr!r}", file=sys.stderr)
        return 1
    print("PASS", args.expected.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
