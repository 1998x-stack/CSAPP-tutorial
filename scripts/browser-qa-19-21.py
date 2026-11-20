#!/usr/bin/env python3
"""Browser QA with actual interactions and three viewports."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
def check(page, n, width):
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.goto((ROOT / f'{n:02}.html').as_uri(), wait_until='load')
    assert page.locator('h1').count() == 1
    images = page.locator('.lesson-figure img')
    assert images.count() == 2
    states = images.evaluate_all('(xs)=>xs.map(x=>[x.complete,x.naturalWidth,x.naturalHeight])')
    assert all(ok and w > 0 and h > 0 for ok,w,h in states), states
    overflow = page.evaluate('document.documentElement.scrollWidth - innerWidth')
    assert overflow <= 1, (n,width,overflow)
    if n == 19:
        control = page.locator('#c19-bytes')
        control.evaluate("(e)=>{e.value='9';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert '偏移量 9' in page.locator('#c19-offset').inner_text()
        page.locator('#c19-separate').click()
        assert '偏移量 0' in page.locator('#c19-offset').inner_text()
    elif n == 20:
        control = page.locator('#c20-chunks')
        control.evaluate("(e)=>{e.value='5';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert 'H | E | L | L | O' in page.locator('#c20-result').inner_text()
    else:
        control = page.locator('#c21-fds')
        control.evaluate("(e)=>{e.value='8';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert '其余 7 条' in page.locator('#c21-ready').inner_text()
    assert not errors, (n,width,errors)
    return {'chapter':n,'width':width,'overflow':overflow,'images_loaded':len(states),'interaction_passed':True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('reports/olah-19-21'))
    out=parser.parse_args().output
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for n in (19,20,21):
            for width in (1440,390,360):
                ctx=browser.new_context(viewport={'width':width,'height':900})
                page=ctx.new_page()
                record=check(page,n,width)
                png=out/f'ch{n}-{width}.png'
                page.screenshot(path=str(png),full_page=True)
                record['screenshot']=str(png)
                results.append(record)
                print('PASS',n,width)
                ctx.close()
        browser.close()
    (out/'report.json').write_text(json.dumps({'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
    main()
