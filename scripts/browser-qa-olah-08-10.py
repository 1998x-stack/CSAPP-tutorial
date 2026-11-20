#!/usr/bin/env python3
"""Chromium browser QA for CSAPP chapters 8–10: layout, MathML, SVG, controls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WIDTHS = (1440, 390, 360)
CHAPTERS = (8, 9, 10)

def verify(page, chapter: int, width: int) -> dict:
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto((ROOT / f"{chapter:02}.html").as_uri(), wait_until="load")
    page.evaluate("document.fonts.ready")
    assert page.locator("main h1").count() == 1
    assert page.locator("main svg[role='img']").count() == 2
    assert page.locator("main figcaption").count() == 2
    svg_state = page.locator("main svg").evaluate_all(
        "(nodes) => nodes.map(x => ({width:x.getBoundingClientRect().width, height:x.getBoundingClientRect().height, title:x.querySelector('title')?.textContent, desc:x.querySelector('desc')?.textContent}))")
    assert all(x["width"] > 0 and x["height"] > 0 and x["title"] and x["desc"] for x in svg_state), svg_state
    math_state = page.locator("main math").evaluate_all(
        "(nodes) => nodes.map(x => ({width:x.getBoundingClientRect().width, height:x.getBoundingClientRect().height, namespace:x.namespaceURI}))")
    if chapter in (9, 10):
        assert math_state and all(x["width"] > 0 and x["height"] > 0 and x["namespace"] == "http://www.w3.org/1998/Math/MathML" for x in math_state), math_state
    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, f"chapter {chapter}, width {width}: document overflows {overflow}px"

    # Every chapter must expose a keyboard-reachable skip link.
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement?.getAttribute('href')")
    assert focused == "#content", (chapter, width, focused)
    page.keyboard.press("Enter")
    assert page.evaluate("window.location.hash") == "#content"

    if chapter == 8:
        page.locator('[data-isa="2"]').click()
        assert page.locator("#isa-choice").inner_text() == "srcA = %rsp"
        assert page.locator('[data-isa="2"]').get_attribute("aria-pressed") == "true"
        page.locator('[data-isa="3"]').focus()
        page.keyboard.press("Enter")
        assert page.locator("#isa-choice").inner_text() == "srcA = RNONE"
    elif chapter == 9:
        assert page.locator("#pipeline-speedup").inner_text() == "3.03×"
        page.locator("#pipeline-n").evaluate(
            "(el) => {el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert page.locator("#pipeline-speedup").inner_text() == "0.91×"
        page.locator('[data-hazard="2"]').click()
        assert "1 个气泡" in page.locator("#hazard-result").inner_text()
    else:
        assert page.locator("#cpe-output").inner_text() == "4.00"
        page.locator("#cpe-k").evaluate(
            "(el) => {el.value='8';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        page.locator("#cpe-l").evaluate(
            "(el) => {el.value='1';el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert page.locator("#cpe-output").inner_text() == "0.50"
    assert not errors, (chapter, width, errors)
    # Print removes navigation/control chrome without hiding the article.
    page.emulate_media(media="print")
    assert page.locator("main h1").is_visible()
    page.emulate_media(media="screen")
    return {"chapter":chapter,"width":width,"overflow_px":overflow,"inline_svg":len(svg_state),
            "math_regions":len(math_state),"keyboard_focus":True,"interactive_assertion":True,"js_errors":errors}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports/olah-08-10"))
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for chapter in CHAPTERS:
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width":width,"height":900},
                                          device_scale_factor=1)
                page = ctx.new_page()
                record = verify(page,chapter,width)
                png = out / f"chapter-{chapter:02}-{width}.png"
                page.screenshot(path=str(png),full_page=True)
                record["screenshot"] = str(png)
                results.append(record)
                print("PASS",chapter,width,"overflow",record["overflow_px"])
                ctx.close()
        browser.close()
    (out / "report.json").write_text(json.dumps({"results":results},
                 ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
