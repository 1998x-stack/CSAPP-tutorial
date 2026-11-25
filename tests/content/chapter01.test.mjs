import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const html = readFileSync(new URL("../../01.html", import.meta.url), "utf8");
const ledger = JSON.parse(readFileSync(new URL("../../docs/evidence/01.json", import.meta.url), "utf8"));

test("chapter 01 has semantic headings, navigation, source links and original diagrams", () => {
  assert.match(html, /<html lang="zh-CN">/);
  assert.equal((html.match(/<h1\b/g) || []).length, 1);
  assert.match(html, /<main\b[^>]*id="content"/);
  assert.match(html, /href="index\.html"/);
  assert.match(html, /href="02\.html"/);
  assert.equal((html.match(/<svg\b/g) || []).length, 4);
  assert.equal((html.match(/<figcaption\b/g) || []).length, 4);
  assert.match(html, /csapp\.cs\.cmu\.edu\/3e/);
  assert.match(html, /gcc\.gnu\.org\/onlinedocs/);
  assert.match(html, /man7\.org\/linux\/man-pages/);
  assert.ok(!/<script[^>]+src=["']https?:/i.test(html), "no externally hosted JavaScript");
  assert.ok(!/<math\b[\s\S]*?<svg\b/i.test(html.split("<math")[1] || ""), "math markup independent of SVG");
  const figurePaths = [
    "../../docs/chapters/assets/01-bits.svg",
    "../../docs/chapters/assets/01-compilation.svg",
    "../../docs/chapters/assets/01-execution.svg"
  ];
  const inlineSvgs = [...html.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].map(x => x[0]);
  assert.equal(inlineSvgs.length, figurePaths.length + 1, "three original diagrams plus the deep-dive figure");
  figurePaths.forEach((path, index) => {
    const asset = readFileSync(new URL(path, import.meta.url), "utf8");
    assert.match(asset, /^<\?xml version="1\.0"/);
    assert.equal(asset.replace(/^<\?xml[^>]*\?>\s*/, "").trim(), inlineSvgs[index].trim());
    assert.match(asset, /xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
    assert.match(asset, /<title\b/);
    assert.match(asset, /<desc\b/);
  });
  const deepSvg = inlineSvgs[figurePaths.length];
  for (const token of ['viewBox=', 'role="img"', '<title', '<desc', 'aria-labelledby="d01t d01d"']) {
    assert.ok(deepSvg.includes(token), 'deep-dive inline SVG ' + token);
  }
  assert.match(html, /id="deep-01"/);
  assert.match(html, /examples\/deep-ch01-04\.py 01/);
  assert.ok(ledger.claims.length >= 6);
  assert.ok(ledger.claims.every(x => x.id && x.claim && x.kind && x.source_url && x.locator && x.status));
});

function fakeElement(initialValue = "") {
  const handlers = {};
  const attrs = {};
  return {
    value: initialValue,
    textContent: "",
    addEventListener(event, cb) { handlers[event] = cb; },
    dispatch(event) { assert.ok(handlers[event], event + " handler missing"); handlers[event](); },
    setAttribute(name, value) { attrs[name] = String(value); },
    getAttribute(name) { return attrs[name] ?? null; }
  };
}

test("step buttons and Amdahl widget update meaningful accessible outputs", () => {
  const ids = new Map();
  for (const key of ["pipeline", "step-heading", "step-explanation", "fraction",
    "factor", "fraction-value", "factor-value", "speedup", "elapsed", "limit"]) {
    ids.set(key, fakeElement());
  }
  ids.get("fraction").value = "60";
  ids.get("factor").value = "10";
  const buttons = Array.from({ length: 4 }, (_, i) => {
    const button = fakeElement();
    button.setAttribute("data-step", String(i));
    button.setAttribute("aria-pressed", String(i === 0));
    return button;
  });
  const document = {
    getElementById(id) { assert.ok(ids.has(id), "Missing " + id); return ids.get(id); },
    querySelectorAll(selector) { assert.equal(selector, "button[data-step]"); return buttons; }
  };
  const scripts = Array.from(html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g));
  assert.equal(scripts.length, 1);
  runInNewContext(scripts[0][1], { document, Math, Number, Array });
  assert.equal(ids.get("speedup").textContent, "2.17×");
  assert.equal(ids.get("elapsed").textContent, "46.0 秒");
  assert.equal(ids.get("limit").textContent, "2.50 倍");
  buttons[2].dispatch("click");
  assert.equal(ids.get("pipeline").getAttribute("data-step-active"), "2");
  assert.equal(buttons[2].getAttribute("aria-pressed"), "true");
  assert.match(ids.get("step-heading").textContent, /汇编/);
  ids.get("fraction").value = "0";
  ids.get("factor").value = "20";
  ids.get("fraction").dispatch("input");
  assert.equal(ids.get("speedup").textContent, "1.00×");
  assert.equal(ids.get("elapsed").textContent, "100.0 秒");
});
