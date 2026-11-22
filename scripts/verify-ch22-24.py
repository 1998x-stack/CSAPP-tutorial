#!/usr/bin/env python3
"""Standalone quality gate for the Olah-style lessons 22–24."""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {22: "sync-ok", 23: "rwlock-ok", 24: "bitlogic-ok"}

class CodeBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_pre = False
        self.in_code = False
        self.count = 0
    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.in_pre = True
        if tag == "code" and self.in_pre:
            self.in_code = True
    def handle_endtag(self, tag):
        if tag == "code" and self.in_code:
            self.count += 1
            self.in_code = False
        if tag == "pre":
            self.in_pre = False

def main():
    for chapter, marker in EXPECTED.items():
        html = (ROOT / f"{chapter:02}.html").read_text(encoding="utf-8")
        assert html.count("<h1>") == 1, f"{chapter}: exactly one h1"
        assert '<main id="chapter-main"' in html and "<article>" in html
        assert 'aria-current="page"' in html
        assert 'href="olah-chapters.css"' in html
        assert f'href="{chapter-1:02}.html"' in html
        assert f'href="{chapter+1:02}.html"' in html
        assert 'href="index.html"' in html
        parser = CodeBlocks()
        parser.feed(html)
        assert parser.count >= 2, f"{chapter}: no meaningful code"
        links = re.findall(r'<img\s+src="(chapter-assets/[^"]+\.svg)"', html)
        expected = 3 if chapter in (22, 23) else 2
        assert len(links) == expected, (chapter, links)
        if chapter in (22, 23):
            assert links[-1] == f"chapter-assets/{chapter}-deep.svg", (chapter, links)
        for rel in links:
            path = ROOT / rel
            svg = ET.parse(path).getroot()
            ns = "{http://www.w3.org/2000/svg}"
            assert svg.get("viewBox") and svg.find(ns + "title") is not None
            assert svg.find(ns + "desc") is not None
            assert not list(svg.iter(ns + "script"))
        scripts = re.findall(r"<script(?:\s[^>]*)?>([\s\S]*?)</script>", html)
        assert len(scripts) == 1, f"{chapter}: expected one native interaction"
        subprocess.run(["node", "--check", "-"], input=scripts[0], text=True, check=True)
        if chapter == 24:
            assert 'xmlns="http://www.w3.org/1998/Math/MathML"' in html
        ledger = json.loads((ROOT / f"docs/evidence/{chapter:02}.json").read_text(encoding="utf-8"))
        assert len(ledger["claims"]) >= 7
        assert all(set(("id","claim","kind","source_url","locator","status","notes")) <= c.keys() for c in ledger["claims"])
        assert all(c["status"] in {"verified","derived","illustrative","unverified"} for c in ledger["claims"])
        with tempfile.TemporaryDirectory(prefix=f"olah-{chapter}-") as folder:
            exe = Path(folder) / "exercise"
            # Explicit paths avoid depending on filename inference.
            names = {22: "olah-ch22-sync.c", 23: "olah-ch23-rwlock.c", 24: "olah-ch24-bitlogic.c"}
            src = ROOT / "examples" / names[chapter]
            subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror","-pedantic","-O2","-pthread",str(src),"-o",str(exe)], check=True, timeout=30)
            output = subprocess.check_output([str(exe)], text=True, timeout=30)
            assert marker in output, (chapter, output)
        print(f"PASS chapter {chapter}: HTML, {expected} SVGs, evidence, JS syntax, compiled C")

if __name__ == "__main__":
    main()
