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
    parser.add_argument("--repeat", default=1, type=int)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.command
    if cmd[:1] == ["--"]:
        cmd = cmd[1:]
    if not cmd:
        parser.error("missing command following --")
    if not (1 <= args.repeat <= 50):
        parser.error("--repeat must be between 1 and 50")
    expected = args.expected.read_text(encoding="utf-8").replace("\r\n", "\n")
    for iteration in range(1, args.repeat + 1):
        try:
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=10, check=False)
        except subprocess.TimeoutExpired:
            print(f"test process timed out on iteration {iteration}", file=sys.stderr)
            return 1
        observed = run.stdout if args.exit_code == 0 else run.stderr
        if (run.returncode != args.exit_code or observed != expected
                or (args.exit_code == 0 and run.stderr)):
            print(f"command: {cmd}; iteration: {iteration}", file=sys.stderr)
            print(f"expected exit: {args.exit_code}, got: {run.returncode}", file=sys.stderr)
            print(f"expected output: {expected!r}", file=sys.stderr)
            print(f"actual output:   {observed!r}", file=sys.stderr)
            print(f"stderr: {run.stderr!r}", file=sys.stderr)
            return 1
    print(f"PASS {args.expected.name} x{args.repeat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
