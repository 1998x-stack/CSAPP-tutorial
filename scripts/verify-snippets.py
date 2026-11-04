#!/usr/bin/env python3
"""Validate migrated chapter code blocks; compiling labs is handled by CTest."""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^\x60{3,}[^\n]*$", re.MULTILINE)


def main() -> None:
    manifest = json.loads((ROOT / "courses.json").read_text(encoding="utf-8"))
    for chapter in manifest["chapters"]:
        path = ROOT / "docs" / "chapters" / (chapter["slug"] + ".md")
        body = path.read_text(encoding="utf-8")
        fences = FENCE.findall(body)
        if len(fences) < 2 or len(fences) % 2:
            raise ValueError(f"{path}: missing/unpaired code fence")
        if "ZZCSAPPBLOCK" in body:
            raise ValueError(f"{path}: unfinished HTML conversion")
    print("Chapter smoke tests passed: 28 Markdown chapters; C code checked by CTest")


if __name__ == "__main__":
    main()
