#!/usr/bin/env python3
"""Browser QA: CSAPP 13–18 causal diagrams and existing interactives at 3 widths."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = tuple(range(13, 19))
WIDTHS = (1440, 390, 360)

def inspect(page, chapter: int, width: int) -> dict:
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto((ROOT / f"{chapter:02}.html").as_uri(), wait_until="load")
    page.evaluate("document.fonts.ready")
    assert page.locator("main h1").count() == 1, (chapter, width, "one title")
    anchor = f"deep-{chapter}"
    section = page.locator("#" + anchor)
    assert section.count() == 1
    assert page.locator(f'a[href="#{anchor}"]').count() >= 1
    image = section.locator(f'img[src="chapter-assets/{chapter}-deep.svg"]')
    assert image.count() == 1, (chapter, width, "new illustrated section")
    image.scroll_into_view_if_needed()
    image.evaluate("(el) => el.decode()")  # force decode of lazy image
    loaded = image.evaluate("(el) => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")
    assert loaded, (chapter, width, "image did not load")
    diagram = section.locator(".deep-figure")
    diagram.focus()
    assert diagram.evaluate("(el) => document.activeElement === el"), (chapter, width, "keyboard focus")
    if chapter <= 15:
        assert page.locator("main svg[role='img']").count() == 1
        root = page.locator(f"#ch{chapter}-state")
        before = page.locator(f"#ch{chapter}-state-description").inner_text()
        button = root.locator('button[data-stage="c"]')
        button.click()
        after = page.locator(f"#ch{chapter}-state-description").inner_text()
        assert before != after, (chapter, width, "original stage output")
        assert button.get_attribute("aria-pressed") == "true"
    else:
        assert page.locator(".lesson-figure img").count() == 3
        if chapter == 16:
            page.locator('[data-sig-case="gap"]').click()
            assert "错过" in page.locator("#sig-schedule").inner_text()
        elif chapter == 17:
            page.locator("#page-offset").evaluate(
                "(el) => {el.value='4095';el.dispatchEvent(new Event('input',{bubbles:true}));}")
            assert "0x12345fff" in page.locator("#page-result").inner_text()
        elif chapter == 18:
            page.locator('[data-request="96"]').click()
            assert "无法满足" in page.locator("#fragment-result").inner_text()

    overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
    assert overflow <= 1, (chapter, width, f"page horizontal overflow: {overflow}px")
    assert not errors, (chapter, width, errors)
    page.emulate_media(media="print")
    assert page.locator("main h1").is_visible(), (chapter, width, "print title")
    page.emulate_media(media="screen")
    page.evaluate("window.scrollTo(0,0)")
    return {"chapter": chapter, "width":width, "overflow_px":overflow,
            "diagram_loaded":loaded, "keyboard_focus":True,
            "original_interactive":True, "console_errors":errors}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports/systems-13-18"))
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for n in CHAPTERS:
            for width in WIDTHS:
                ctx = browser.new_context(viewport={"width":width,"height":900}, device_scale_factor=1)
                page = ctx.new_page()
                rec = inspect(page,n,width)
                shot = out / f"chapter-{n}-{width}.png"
                page.screenshot(path=str(shot), full_page=True)
                rec["screenshot"] = str(shot)
                records.append(rec)
                print("PASS",n,width,"overflow",rec["overflow_px"])
                ctx.close()
        browser.close()
    (out/"report.json").write_text(
        json.dumps({"results":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
