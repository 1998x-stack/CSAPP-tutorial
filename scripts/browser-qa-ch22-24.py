#!/usr/bin/env python3
"""Playwright browser check for chapters 22–24 at desktop and mobile widths."""
from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "olah-22-24"

def verify(page, chapter, width):
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto((ROOT / f"{chapter:02}.html").as_uri(), wait_until="load")
    page.evaluate("document.fonts.ready")
    assert page.locator("h1").count() == 1
    imgs = page.locator(".lesson-figure img")
    assert imgs.count() == 2
    for i in range(2):
        assert imgs.nth(i).evaluate("(el) => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")
    assert page.evaluate("document.documentElement.scrollWidth - innerWidth") <= 1, (chapter,width,"overflow")
    if chapter == 22:
        before = page.locator("#schedule-result").inner_text()
        page.get_by_role("button", name="交错读写").click()
        after = page.locator("#schedule-result").inner_text()
        assert before != after and "最终 8" in after
        assert page.get_by_role("button", name="交错读写").get_attribute("aria-pressed") == "true"
    elif chapter == 23:
        page.get_by_role("button", name="提交任务").click()
        assert "队列 1/2" in page.locator("#pool-status").inner_text()
        page.get_by_role("button", name="领取任务").click()
        assert "忙碌" in page.locator("#pool-status").inner_text()
        page.get_by_role("button", name="完成任务").click()
        assert "已完成 1" in page.locator("#pool-status").inner_text()
    else:
        page.get_by_role("button", name="切换 x：0").click()
        assert "x=1, y=0" in page.locator("#xor-result").inner_text()
        page.get_by_role("button", name="切换 y：0").click()
        assert "x=1, y=1" in page.locator("#xor-result").inner_text()
        math = page.locator("math")
        assert math.count() >= 1
        assert math.first.evaluate("(el) => el.namespaceURI === 'http://www.w3.org/1998/Math/MathML' && el.getBoundingClientRect().height > 0")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement !== document.body")
    assert not errors, (chapter,width,errors)
    return {"chapter":chapter,"width":width,"overflow_px":0,"images_ok":2,"interaction_ok":True,"js_errors":errors}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for chapter in (22,23,24):
            for width in (1440,390,360):
                context = browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1)
                page = context.new_page()
                record = verify(page, chapter, width)
                name = OUT / f"chapter-{chapter:02}-{width}.png"
                page.screenshot(path=str(name), full_page=True)
                record["screenshot"] = name.name
                records.append(record)
                print("PASS",chapter,width)
                context.close()
        browser.close()
    (OUT / "report.json").write_text(json.dumps({"results":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
