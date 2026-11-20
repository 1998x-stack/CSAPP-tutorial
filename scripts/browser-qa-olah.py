#!/usr/bin/env python3
"""Headless QA for the three progressive-disclosure lessons.

Run: pip install playwright==1.55.0
     python -m playwright install chromium
     python scripts/browser-qa-olah.py --output reports/olah
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WIDTHS = (1440, 390, 360)
CHAPTERS = (2, 3, 4)

def verify(page, chapter: int, width: int) -> dict:
    errors: list[str] = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append("console: " + msg.text) if msg.type == "error" else None)
    page.goto((ROOT / f"{chapter:02}.html").as_uri(), wait_until="load")
    page.locator(".lesson-figure img").first.wait_for(state="visible")
    page.evaluate("document.fonts.ready")
    assert page.locator("h1").count() == 1, f"{chapter}: expected single H1"
    assert page.locator(".lesson-figure img").count() == 3
    image_state = page.locator(".lesson-figure img").evaluate_all(
        "(items) => items.map(x => ({ready:x.complete, width:x.naturalWidth, height:x.naturalHeight}))")
    assert all(x["ready"] and x["width"] > 0 and x["height"] > 0 for x in image_state), (
        chapter, width, image_state)
    sizes = page.locator(".math-scroll math").evaluate_all(
        "(items) => items.map(x => ({width:x.getBoundingClientRect().width, height:x.getBoundingClientRect().height, namespace:x.namespaceURI}))")
    assert all(x["width"] > 0 and x["height"] > 0 and x["namespace"] == "http://www.w3.org/1998/Math/MathML" for x in sizes), (
        chapter, width, sizes)
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"{chapter} viewport {width}: document horizontal overflow {overflow}px"
    if chapter == 2:
        control = page.locator("#byte-value")
        before = page.locator("#byte-output").inner_text()
        control.evaluate("(el) => {el.value='0';el.dispatchEvent(new Event('input', {bubbles:true}));}")
        after = page.locator("#byte-output").inner_text()
        assert before != after and "无符号 0" in after, (before, after)
    elif chapter == 3:
        page.locator('[data-f32="0.2"]').click()
        after = page.locator("#float-bits").inner_text()
        assert "0x3e4ccccd" in after, after
        assert page.locator('[data-f32="0.2"]').get_attribute("aria-pressed") == "true"
    else:
        before = page.locator("#addr-result").inner_text()
        page.locator("#idx").evaluate("(el) => {el.value='12';el.dispatchEvent(new Event('input', {bubbles:true}));}")
        after = page.locator("#addr-result").inner_text()
        assert before != after and "0x1060" in after, (before, after)
    assert not errors, f"{chapter} viewport {width} JS errors: {errors}"
    return {"chapter":chapter,"width":width,"overflow_px":overflow,
            "images_loaded":len(image_state),"math_regions":len(sizes),
            "interactive_assertion":True,"js_errors":errors}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("reports/olah"))
    out = p.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for chapter in CHAPTERS:
            for width in WIDTHS:
                context = browser.new_context(viewport={"width":width,"height":900},
                                              device_scale_factor=1)
                page = context.new_page()
                record = verify(page, chapter, width)
                file = out / f"chapter-{chapter:02}-{width}.png"
                page.screenshot(path=str(file), full_page=True)
                record["screenshot"] = str(file)
                results.append(record)
                print("PASS", chapter, width, "overflow", record["overflow_px"])
                context.close()
        browser.close()
    (out / "report.json").write_text(
        json.dumps({"results":results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

if __name__ == "__main__":
    main()
