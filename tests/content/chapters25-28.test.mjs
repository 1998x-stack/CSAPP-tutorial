import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { runInNewContext } from "node:vm";

const root = resolve(import.meta.dirname, "../..");
const read = p => readFileSync(resolve(root, p), "utf8");
const chapters = [25, 26, 27, 28];
const figure = {25:"25-cache.svg",26:"26-proxy.svg",27:"27-layers.svg",28:"28-state.svg"};
for (const chapter of chapters) {
  test("chapter " + chapter + ": heading, structure, source records and standalone SVG", () => {
    const html = read(chapter + ".html");
    assert.match(html, /<html lang="zh-CN">/);
    assert.match(html, /<body class="olah-lesson">/);
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.match(html, /<main\b[^>]*id="chapter-main"/);
    assert.match(html, /class="chapter-toc"/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /href="index\.html"/);
    assert.match(html, /<section\b/);
    assert.match(html, /<figcaption>/);
    assert.match(html, /csapp\.cs\.cmu\.edu|docs\.riscv\.org|man7\.org/);
    assert.ok(!/<script\b[^>]+src=["']https?:/i.test(html), "offline JavaScript only");
    assert.ok(!/(?:\d{2},?000\+? req\/s|10万连接已实现)/i.test(html), "no false benchmark claim");
    assert.match(html, new RegExp('src="chapter-assets/' + figure[chapter].replace(".", "\\.") + '"'));
    const svg = read("chapter-assets/" + figure[chapter]);
    assert.match(svg, /xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
    assert.match(svg, /viewBox="/);
    assert.match(svg, /<title\b/);
    assert.match(svg, /<desc\b/);
    assert.match(svg, /<\/svg>\s*$/);
    const ledger = JSON.parse(read("evidence/" + chapter + ".json"));
    assert.equal(ledger.chapter, chapter);
    assert.ok(ledger.claims.length >= 4);
    assert.ok(ledger.claims.every(c => c.id && c.claim && c.source_url && c.locator && c.status));
    const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
    assert.equal(scripts.length, 1, "one local interaction script");
    assert.doesNotThrow(() => new Function(scripts[0][1]));
  });
}

function fakeElement(value = "", data = {}) {
  const events = {}, attributes = {};
  return {
    value, dataset:data, textContent:"",
    addEventListener(event, handler) { events[event] = handler; },
    trigger(event) { assert.ok(events[event], event + " handler"); events[event](); },
    setAttribute(k,v) { attributes[k] = String(v); },
    getAttribute(k) { return attributes[k] ?? null; }
  };
}
function run(chapter, selectors, initial = {}) {
  const html = read(chapter + ".html");
  const js = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)][0][1];
  const ids = new Map(Object.entries(initial).map(([k,v])=>[k,fakeElement(v)]));
  const buttons = selectors.buttons || [];
  const doc = {
    getElementById(k) {
      if (!ids.has(k)) ids.set(k,fakeElement());
      return ids.get(k);
    },
    querySelectorAll(sel) {
      assert.equal(sel,selectors.selector);
      return buttons;
    }
  };
  runInNewContext(js,{document:doc,Math,Number,Array,String});
  return {ids,buttons};
}
test("25: cache replay counts hits, misses and eviction deterministically", () => {
  const buttons=[1,2,3,4].map(n=>fakeElement("",{cacheStep:String(n)}));
  const {ids}=run(25,{buttons,selector:"[data-cache-step]"});
  assert.match(ids.get("cache-trace-output").textContent,/hit 0 \/ miss 1 \/ eviction 0/);
  buttons[3].trigger("click");
  assert.match(ids.get("cache-trace-output").textContent,/hit 1 \/ miss 3 \/ eviction 1/);
  assert.equal(buttons[3].getAttribute("aria-pressed"),"true");
});
test("26: cache policy distinguishes no-store, private and vary", () => {
  const buttons=["public","private","nostore","vary"].map(policy=>fakeElement("",{policy}));
  const {ids}=run(26,{buttons,selector:"[data-policy]"});
  buttons[2].trigger("click");
  assert.match(ids.get("policy-output").textContent,/不能保存/);
  buttons[1].trigger("click");
  assert.match(ids.get("policy-output").textContent,/不能进入共享缓存/);
  buttons[3].trigger("click");
  assert.match(ids.get("policy-output").textContent,/Accept-Language/);
});
test("27: arithmetic intensity moves from bandwidth to compute limit", () => {
  const {ids}=run(27,{selector:"",buttons:[]},{"roofline-intensity":"1"});
  assert.match(ids.get("roofline-result").textContent,/2 GFLOP\/s，内存带宽限制/);
  ids.get("roofline-intensity").value="4";
  ids.get("roofline-intensity").trigger("input");
  assert.match(ids.get("roofline-result").textContent,/8 GFLOP\/s，计算峰值限制/);
});
test("28: connection state changes and stays accessible", () => {
  const buttons=[0,1,2,3].map(connStep=>fakeElement("",{connStep:String(connStep)}));
  const {ids}=run(28,{buttons,selector:"[data-conn-step]"});
  assert.match(ids.get("connection-state-output").textContent,/READING/);
  buttons[2].trigger("click");
  assert.match(ids.get("connection-state-output").textContent,/Keep-Alive/);
  buttons[3].trigger("click");
  assert.match(ids.get("connection-state-output").textContent,/CLOSED/);
  assert.equal(buttons[3].getAttribute("aria-pressed"),"true");
});
