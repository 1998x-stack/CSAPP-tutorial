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
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    "labs/bit-operations/representation.c": "endianness=",
    "labs/cache/cache_geometry.c": "set=1 offset=12",
    "examples/olah-ch02-integers.c": "integer-examples=ok",
    "examples/olah-ch03-floats.c": "floating-examples=ok",
    "examples/olah-ch04-machine.c": "machine-examples=ok",
    "examples/olah-ch16-signals.c": "signal-delivered=1",
    "examples/olah-ch17-vm.c": "vm-decomposition=ok",
    "examples/olah-ch18-allocator.c": "mapping-released=1",
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


def check_illustrated_chapters() -> None:
    """Inspect SVGs and ensure chapter inline scripts are syntactically valid."""
    for chapter in (2, 3, 4, 16, 17, 18):
        html = (ROOT / f"{chapter:02}.html").read_text(encoding="utf-8")
        if "<main id=\"chapter-main\"" not in html or "<article>" not in html:
            raise AssertionError(f"chapter {chapter}: semantic article missing")
        if "<math " not in html:
            raise AssertionError(f"chapter {chapter}: MathML missing")
        assets = re.findall(r'<img\s+src="(chapter-assets/[^"]+\.svg)"', html)
        if len(assets) != 3:
            raise AssertionError(f"chapter {chapter}: expected 3 original SVGs")
        for name in assets:
            svg = ROOT / name
            tree = ET.parse(svg)
            root = tree.getroot()
            if not root.get("viewBox") or root.find("{http://www.w3.org/2000/svg}title") is None:
                raise AssertionError(f"{name}: missing viewBox/title")
            if root.find("{http://www.w3.org/2000/svg}desc") is None:
                raise AssertionError(f"{name}: no standalone description")
        inline = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", html)
        for js in inline:
            subprocess.run(["node", "--check", "-"], input=js, text=True, check=True, timeout=10)


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
    check_illustrated_chapters()
    check_c()
    print("Snippet checks passed: 28 chapter code sections, 18 SVGs and 8 compiled C examples")

