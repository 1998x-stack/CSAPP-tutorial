#!/usr/bin/env python3
"""Screenshot + interaction QA for Olah-style CSAPP chapters 25–28.

Run with: pip install playwright==1.65.2
          python -m playwright install chromium
          python scripts/browser-qa-ch25-28.py --output reports/olah-25-28
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = (25, 26, 27, 28)
WIDTHS = (1440, 390, 360)


def check(page, chapter: int, width: int) -> dict:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    page.goto((ROOT / f"{chapter:02}.html").as_uri(), wait_until="load")
    page.locator(".lesson-figure img").first.wait_for(state="visible")
    page.evaluate("document.fonts.ready")
    assert page.locator("h1").count() == 1, f"{chapter}: expected one h1"
    assert page.locator("main#chapter-main").count() == 1
    assert page.locator(".lesson-figure figcaption").count() == 1
    img = page.locator(".lesson-figure img").first.evaluate(
        "(e) => ({complete:e.complete,w:e.naturalWidth,h:e.naturalHeight})")
    assert img["complete"] and img["w"] > 0 and img["h"] > 0, (chapter, width, img)
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    assert overflow <= 1, f"{chapter} at {width}px overflows by {overflow}px"

    if chapter == 25:
        out = page.locator("#cache-trace-output")
        assert "miss 1" in out.inner_text()
        page.locator('[data-cache-step="4"]').click()
        assert "hit 1 / miss 3 / eviction 1" in out.inner_text()
        assert page.locator('[data-cache-step="4"]').get_attribute("aria-pressed") == "true"
    elif chapter == 26:
        page.locator('[data-policy="nostore"]').click()
        assert "不能保存" in page.locator("#policy-output").inner_text()
        page.locator('[data-policy="vary"]').click()
        assert "Accept-Language" in page.locator("#policy-output").inner_text()
    elif chapter == 27:
        range_input = page.locator("#roofline-intensity")
        range_input.evaluate("(el) => {el.value='4';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "8 GFLOP/s，计算峰值限制" in page.locator("#roofline-result").inner_text()
    elif chapter == 28:
        page.locator('[data-conn-step="3"]').click()
        assert "CLOSED" in page.locator("#connection-state-output").inner_text()
        assert page.locator('[data-conn-step="3"]').get_attribute("aria-pressed") == "true"
    assert not errors, (chapter, width, errors)
    return {"chapter": chapter, "width": width, "overflow_px": overflow,
            "image_loaded": True, "interaction_passed": True, "js_errors": errors}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("reports/olah-25-28"))
    out = ap.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for chapter in CHAPTERS:
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 900},
                                              device_scale_factor=1)
                page = context.new_page()
                record = check(page, chapter, width)
                path = out / f"chapter-{chapter}-{width}.png"
                page.screenshot(path=str(path), full_page=True)
                record["screenshot"] = str(path)
                results.append(record)
                print("PASS", chapter, width, "overflow", record["overflow_px"])
                context.close()
        browser.close()
    (out / "report.json").write_text(
        json.dumps({"results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf8")


if __name__ == "__main__":
    main()
