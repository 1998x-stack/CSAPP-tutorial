#!/usr/bin/env python3
"""Chromium QA for chapters 19–23: deep figures and original UI at 3 widths."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
CHAPTERS=tuple(range(19,24))
WIDTHS=(1440,390,360)

def inspect(page,n,width):
    errors=[]
    page.on("pageerror",lambda error:errors.append(str(error)))
    page.on("console",lambda event:errors.append(event.text) if event.type=="error" else None)
    page.goto((ROOT/f"{n}.html").as_uri(),wait_until="load")
    page.evaluate("document.fonts.ready")
    assert page.locator("main h1").count()==1,(n,width,"single h1")
    assert page.locator("main .lesson-figure img").count()==2,(n,width,"two original figures")
    section=page.locator(f"#deep-{n}")
    assert section.count()==1
    assert page.locator(f'a[href="#deep-{n}"]').count()>=1
    image=section.locator(f'img[src="chapter-assets/{n}-deep.svg"]')
    assert image.count()==1
    image.scroll_into_view_if_needed()
    image.evaluate("(image)=>image.decode()")
    assert image.evaluate("(image)=>image.complete && image.naturalWidth>0 && image.naturalHeight>0"),(n,width,"image load")
    figure=section.locator(".deep-figure")
    figure.focus()
    assert figure.evaluate("(el)=>document.activeElement===el"),(n,width,"keyboard focus")
    # Preserve the original interactive teaching widget on every chapter.
    if n==19:
        page.locator("#c19-bytes").evaluate(
            "(e)=>{e.value='9';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "偏移量 9" in page.locator("#c19-offset").inner_text()
        page.locator("#c19-separate").click()
        assert "偏移量 0" in page.locator("#c19-offset").inner_text()
    elif n==20:
        page.locator("#c20-chunks").evaluate(
            "(e)=>{e.value='5';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "H | E | L | L | O" in page.locator("#c20-result").inner_text()
    elif n==21:
        page.locator("#c21-fds").evaluate(
            "(e)=>{e.value='8';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert "其余 7 条" in page.locator("#c21-ready").inner_text()
    elif n==22:
        page.locator('button[data-plan="locked"]').click()
        assert "最终 9" in page.locator("#schedule-result").inner_text()
        assert page.locator('button[data-plan="locked"]').get_attribute("aria-pressed")=="true"
    elif n==23:
        page.locator('button[data-pool="submit"]').click()
        page.locator('button[data-pool="submit"]').click()
        assert "队列 2/2" in page.locator("#pool-status").inner_text()
        page.locator('button[data-pool="close"]').click()
        assert "停止接单" in page.locator("#pool-status").inner_text()
        page.locator('button[data-pool="start"]').click()
        page.locator('button[data-pool="finish"]').click()
        assert "已完成 1" in page.locator("#pool-status").inner_text()
    overflow=page.evaluate("document.documentElement.scrollWidth-window.innerWidth")
    assert overflow<=1,(n,width,f"horizontal overflow {overflow}")
    assert not errors,(n,width,errors)
    page.emulate_media(media="print")
    assert page.locator("main h1").is_visible()
    page.emulate_media(media="screen")
    page.evaluate("window.scrollTo(0,0)")
    return {"chapter":n,"width":width,"overflow_px":overflow,
            "new_svg_loaded":True,"original_widget":True,
            "figure_keyboard_focus":True,"errors":errors}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=Path("reports/deep-19-23"))
    output=parser.parse_args().output
    output.mkdir(parents=True,exist_ok=True)
    records=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for n in CHAPTERS:
            for width in WIDTHS:
                ctx=browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1)
                page=ctx.new_page()
                record=inspect(page,n,width)
                path=output/f"chapter-{n}-{width}.png"
                page.screenshot(path=str(path),full_page=True)
                record["screenshot"]=str(path)
                records.append(record)
                print("PASS",n,width,"overflow",record["overflow_px"])
                ctx.close()
        browser.close()
    (output/"report.json").write_text(
        json.dumps({"results":records},ensure_ascii=False,indent=2)+"\n",encoding="utf8")

if __name__=="__main__":
    main()
