#!/usr/bin/env python3
"""Compile and run C11 correctness examples for storage hierarchy chapters.

These are algorithm/bit-mapping invariant tests, not performance benchmarks.
"""
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAMS = {
    "labs/cache/locality.c": "row=32640 col=32640",
    "labs/cache/cache_mapping.c": "direct=MMM two-way=MMH",
    "labs/cache/matmul_block.c": "naive and tiled results match",
}


def main():
    compiler = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="csapp-cache-") as temp:
        for index, (relative, expected) in enumerate(PROGRAMS.items()):
            executable = pathlib.Path(temp) / ("example" + str(index))
            subprocess.run(
                [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", str(ROOT / relative), "-o", str(executable)],
                check=True, capture_output=True, text=True, timeout=30
            )
            completed = subprocess.run([str(executable)], check=True, capture_output=True, text=True, timeout=10)
            assert completed.stdout.strip() == expected, (relative, completed.stdout)
            print(relative, "OK:", expected)


if __name__ == "__main__":
    main()
