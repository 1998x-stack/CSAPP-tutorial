#!/usr/bin/env python3
"""Real Chromium QA for CSAPP lessons 05–07, including responsive figures and widgets."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = (5, 6, 7)
WIDTHS = (1440, 390, 360)

def check(page, n: int, width: int) -> dict:
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto((ROOT / f"{n:02}.html").as_uri(), wait_until="load")
    page.evaluate("document.fonts.ready")
    assert page.locator("h1").count() == 1, (n, width, "single H1")
    assert page.locator(".olah-lesson h2").count() >= 5, (n, width, "sections")
    assert page.locator(".diagram img").count() == 2, (n, width, "figures")
    image_state = page.locator(".diagram img").evaluate_all(
        "(items) => items.map(x => ({ready:x.complete, w:x.naturalWidth, h:x.naturalHeight}))")
    assert all(x["ready"] and x["w"] > 0 and x["h"] > 0 for x in image_state), image_state
    math = page.locator(".equation math").evaluate_all(
        "(items) => items.map(x => ({w:x.getBoundingClientRect().width, "
        "h:x.getBoundingClientRect().height, ns:x.namespaceURI}))")
    if n in (6, 7):
        assert math and all(m["w"] > 0 and m["h"] > 0 and
            m["ns"] == "http://www.w3.org/1998/Math/MathML" for m in math), math
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, (n, width, f"document overflow: {overflow}")
    if n == 5:
        before = page.locator("#signed-output").inner_text()
        page.locator("#signed-x").evaluate(
            "(el) => {el.value='7';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        after = page.locator("#signed-output").inner_text()
        assert before != after and "无符号 7" in after, (before, after)
    elif n == 6:
        page.locator("#factorial-n").evaluate(
            "(el) => {el.value='6';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "720" in page.locator("#factorial-output").inner_text()
    else:
        page.locator("#col-index").evaluate(
            "(el) => {el.value='3';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "44 字节" in page.locator("#matrix-output").inner_text()
    assert not errors, (n, width, errors)
    return {"chapter":n, "width":width, "overflow_px":overflow,
            "images":image_state, "math_regions":len(math),
            "interaction_passed":True, "js_errors":errors}

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, default=Path("reports/olah-05-07"))
    out = p.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for n in CHAPTERS:
            for width in WIDTHS:
                context = browser.new_context(viewport={"width":width,"height":900},
                                              device_scale_factor=1)
                page = context.new_page()
                record = check(page, n, width)
                screenshot = out / f"chapter-{n:02}-{width}.png"
                page.screenshot(path=str(screenshot), full_page=True)
                record["screenshot"] = str(screenshot)
                if width == 1440:
                    page.emulate_media(media="print")
                    print_overflow = page.evaluate(
                        "document.documentElement.scrollWidth - window.innerWidth")
                    assert print_overflow <= 1, (n, "print overflow", print_overflow)
                    record["print_overflow_px"] = print_overflow
                results.append(record)
                print("PASS", n, width, "overflow", record["overflow_px"])
                context.close()
        browser.close()
    (out / "report.json").write_text(
        json.dumps({"results":results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

if __name__ == "__main__":
    main()
