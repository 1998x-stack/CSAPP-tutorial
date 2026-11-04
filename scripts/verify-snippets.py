#!/usr/bin/env python3
"""V0.1 smoke tests for runnable standalone C examples and HTML code sections.

Inline book fragments are illustrative, not guaranteed standalone programs.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "labs/bit-operations/representation.c": "endianness=",
    "labs/cache/cache_geometry.c": "set=1 offset=12",
}


class SnippetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_pre = False
        self.in_code = False
        self.code_count = 0
        self.current = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "pre":
            self.in_pre = True
        if self.in_pre and tag == "code":
            self.in_code = True
            self.current = ""

    def handle_data(self, data: str) -> None:
        if self.in_code:
            self.current += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "code" and self.in_code:
            if not self.current.strip():
                raise ValueError("empty <pre><code> block")
            self.code_count += 1
            self.in_code = False
        if tag == "pre":
            self.in_pre = False


def check_html() -> None:
    for index in range(1, 29):
        path = ROOT / f"{index:02}.html"
        parser = SnippetParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if parser.code_count == 0:
            raise ValueError(f"{path.name}: no code samples found")


def check_c() -> None:
    compiler = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="csapp-v01-") as tmp:
        for source, expected in SOURCES.items():
            executable = Path(tmp) / Path(source).stem
            subprocess.run(
                [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-O2", str(ROOT / source), "-o", str(executable)],
                check=True,
                timeout=30,
            )
            output = subprocess.check_output([str(executable)], text=True, timeout=10)
            if expected not in output:
                raise AssertionError(f"{source}: expected {expected!r}, got {output!r}")


if __name__ == "__main__":
    check_html()
    check_c()
    print("Snippet checks passed: 28 chapter code sections and 2 compiled C examples")

