#!/usr/bin/env python3
"""Verify migrated fenced snippets exist, and compile explicitly standalone C examples."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "labs/bit-operations/representation.c": "endianness=",
    "labs/cache/cache_geometry.c": "set=1 offset=12",
}


def check_markdown() -> None:
    manifest = json.loads((ROOT / "courses.json").read_text(encoding="utf-8"))
    for chapter in manifest["chapters"]:
        path = ROOT / "docs" / "chapters" / (chapter["slug"] + ".md")
        body = path.read_text(encoding="utf-8")
        fenced = re.findall(r"^\x60{3,}(\w*)\n[\s\S]*?^\x60{3,}\s*$", body, re.M)
        if not fenced:
            raise ValueError(f"{path}: no code samples")
        if "ZZCSAPPBLOCK" in body:
            raise ValueError(f"{path}: unfinished HTML conversion")


def check_c() -> None:
    compiler = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="csapp-v02-") as tmp:
        for source, expected in SOURCES.items():
            executable = Path(tmp) / Path(source).stem
            subprocess.run([
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-pedantic", "-O2", str(ROOT / source), "-o", str(executable)
            ], check=True, timeout=30)
            actual = subprocess.check_output([str(executable)], text=True, timeout=10)
            if expected not in actual:
                raise AssertionError(f"{source}: expected {expected!r}; got {actual!r}")


if __name__ == "__main__":
    check_markdown()
    check_c()
    print("Snippet smoke tests passed: 28 Markdown chapters, 2 compiled C programs")

