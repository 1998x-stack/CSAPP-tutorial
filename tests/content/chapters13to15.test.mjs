import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";

const read = path => readFileSync(new URL(path, import.meta.url), "utf8");
const chapters = [
  ["13", "13-linking.svg", 6],
  ["14", "14-dynamic-linking.svg", 5],
  ["15", "15-process-lifecycle.svg", 5],
];

for (const [number, svgName, expectedHeads] of chapters) {
  test("chapter " + number + " keeps semantic narrative, standalone diagram and evidence", () => {
    const html = read("../../" + number + ".html");
    const asset = read("../../docs/chapters/assets/" + svgName);
    const ledger = JSON.parse(read("../../docs/chapters/" + number + "-evidence.json"));
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.equal((html.match(/<h2\b/g) || []).length, expectedHeads);
    assert.match(html, /<html lang="zh-CN">/);
    assert.match(html, /<main id="content"><article class="chapter-olah">/);
    assert.match(html, /href="chapter-olah\.css"/);
    assert.match(html, /class="skip-link"/);
    assert.match(html, /class="chapter-map"/);
    assert.match(html, /href="index\.html"/);
    assert.equal((html.match(/<svg\b/g) || []).length, 1);
    assert.equal((html.match(/<figcaption\b/g) || []).length, 1);
    const inlineSvg = html.match(/<svg\b[\s\S]*?<\/svg>/);
    assert.ok(inlineSvg);
    assert.equal(asset.replace(/^<\?xml[^>]*\?>\s*/, "").trim(), inlineSvg[0]);
    assert.match(asset, /<title\b/);
    assert.match(asset, /<desc\b/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /aria-pressed="true"/);
    assert.equal((html.match(/<button type="button" data-stage=/g) || []).length, 3);
    assert.ok(!/<script\b[^>]*src=["']https?:/i.test(html));
    assert.ok(!html.includes("原创图解 · 单文件离线 HTML"));
    assert.ok(ledger.claims.length >= 6);
    assert.ok(ledger.claims.every(c =>
      c.id && c.claim && c.kind && c.source_url && c.locator &&
      ["verified", "derived", "illustrative", "unverified"].includes(c.status)));
  });

  test("chapter " + number + " accessible stage buttons change visible explanation", () => {
    const html = read("../../" + number + ".html");
    const buttons = ["a", "b", "c"].map(stage => {
      const events = {};
      const attrs = { "aria-pressed": stage === "a" ? "true" : "false" };
      return {
        dataset: { stage },
        addEventListener(name, fn) { events[name] = fn; },
        setAttribute(name, value) { attrs[name] = value; },
        getAttribute(name) { return attrs[name]; },
        click() { events.click(); }
      };
    });
    const root = {
      dataset: { stage: "a" },
      querySelectorAll(selector) {
        assert.equal(selector, "button[data-stage]");
        return buttons;
      }
    };
    const live = { textContent: "default" };
    const document = {
      getElementById(id) {
        return id.endsWith("-description") ? live : root;
      }
    };
    const script = html.match(/<script>\s*([\s\S]*?)<\/script>/);
    assert.ok(script, "expected inline progressive enhancement script");
    runInNewContext(script[1], { document });
    buttons[2].click();
    assert.equal(root.dataset.stage, "c");
    assert.equal(buttons[2].getAttribute("aria-pressed"), "true");
    assert.equal(buttons[0].getAttribute("aria-pressed"), "false");
    assert.notEqual(live.textContent, "default");
    assert.ok(live.textContent.length > 15);
  });
}
