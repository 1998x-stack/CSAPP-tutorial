#!/usr/bin/env python3
"""Chromium smoke tests for the static homepage and progressive enhancement.

Install with: pip install playwright==1.65.2
              python -m playwright install chromium
Run: python scripts/browser-qa-home.py
"""
from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "homepage"

def verify(page, width):
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto((ROOT / "index.html").as_uri(), wait_until="load")
    assert page.locator("h1").count() == 1
    assert page.locator(".chapter-card").count() == 28
    assert page.locator(".stage").count() == 7
    assert page.locator(".chapter-card:visible").count() == 28
    overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
    assert overflow <= 1, ("overflow", width, overflow)
    page.locator("#chapter-search").fill("Pthreads")
    assert page.locator(".chapter-card:visible").count() == 1
    assert page.locator('.chapter-card:visible').first.get_attribute("href") == "22.html"
    page.locator("#chapter-search").fill("")
    page.locator('button[data-filter="memory"]').click()
    assert page.locator(".chapter-card:visible").count() == 2
    page.locator('.stage[data-route="practice"]').click()
    assert page.locator(".chapter-card:visible").count() == 5
    page.locator('#chapter-search').fill('不存在的关键词')
    assert page.locator('#empty-state').is_visible()
    page.locator('#chapter-search').fill('')
    page.locator('button[data-filter="all"]').click()
    assert page.locator(".chapter-card:visible").count() == 28
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement !== document.body")
    assert not errors, (width, errors)
    return {"width":width,"chapter_links":28,"learning_stages":7,
            "overflow_px":overflow,"search_ok":True,"filter_ok":True,"js_errors":errors}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for width in (1440, 390, 360):
            context = browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1)
            page = context.new_page()
            result = verify(page, width)
            filename = f"homepage-{width}.png"
            page.screenshot(path=str(OUT / filename), full_page=True)
            result["screenshot"] = filename
            records.append(result)
            context.close()
            print("PASS homepage",width)
        nojs = browser.new_context(viewport={"width":390,"height":900}, java_script_enabled=False)
        page = nojs.new_page()
        page.goto((ROOT / "index.html").as_uri(),wait_until="load")
        assert page.locator(".chapter-card:visible").count() == 28
        assert page.locator("#catalog-tools").is_hidden()
        assert page.locator(".chapter-card").first.get_attribute("href") == "01.html"
        assert page.evaluate("document.documentElement.scrollWidth - innerWidth") <= 1
        records.append({"mode":"no-javascript","width":390,"chapter_links":28,"passed":True})
        nojs.close()
        browser.close()
    (OUT / "report.json").write_text(json.dumps({"results":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

if __name__ == "__main__":
    main()
