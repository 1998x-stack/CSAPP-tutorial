import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { runInNewContext } from "node:vm";

const root = resolve(import.meta.dirname, "../..");
const read = p => readFileSync(join(root, p), "utf8");
const targets = [
  {id: "08", diagrams: ["08-encoding.svg", "08-seq.svg"], controls: 4},
  {id: "09", diagrams: ["09-timeline.svg", "09-load-use.svg"], controls: 3},
  {id: "10", diagrams: ["10-cpe.svg", "10-ilp.svg"], controls: 0}
];

for (const ch of targets) {
  test("chapter " + ch.id + " has semantic narrative and independent SVGs", () => {
    const html = read(ch.id + ".html");
    assert.match(html, /<html lang="zh-CN">/);
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.match(html, /<main\b[^>]*id="content"/);
    assert.match(html, /<nav class="inline-toc"/);
    assert.match(html, new RegExp('aria-current="page" href="' + ch.id + '\\.html"'));
    assert.match(html, /<figcaption\b/);
    assert.match(html, /csapp\.cs\.cmu\.edu\/3e/);
    assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
    const svg = [...html.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].map(m => m[0]);
    assert.equal(svg.length, 2);
    for (let i = 0; i < svg.length; ++i) {
      const asset = read("docs/chapters/assets/" + ch.diagrams[i]);
      assert.match(asset, /^<\?xml version="1\.0"/);
      assert.equal(asset.replace(/^<\?xml[^>]*\?>\s*/, "").trim(), svg[i].trim());
      assert.match(asset, /xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
      assert.match(asset, /<title\b/);
      assert.match(asset, /<desc\b/);
      assert.match(svg[i], /viewBox=/);
    }
    if (ch.id !== "08") assert.match(html, /<math\b/);
    const ledger = JSON.parse(read("docs/chapters/" + ch.id + "-evidence.json"));
    assert.ok(ledger.claims.length >= 6);
    assert.ok(ledger.claims.every(c => c.id && c.claim && c.source_url && c.locator && c.status));
    assert.equal([...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].length, 1);
  });
}

function element(value = "") {
  const events = {}, attrs = {};
  return {
    value, textContent: "",
    addEventListener(event, fn) { events[event] = fn; },
    trigger(event) { assert.ok(events[event]); events[event](); },
    getAttribute(name) { return attrs[name] ?? null; },
    setAttribute(name, val) { attrs[name] = String(val); }
  };
}
function run(chapter, values, count) {
  const ids = new Map(Object.entries(values).map(([key,value]) => [key,element(value)]));
  const buttons = Array.from({length:count}, (_,i) => {
    const b = element(); b.setAttribute("data-"+(chapter==="08"?"isa":"hazard"),String(i)); return b;
  });
  const document = {
    getElementById(id) {
      if (!ids.has(id)) ids.set(id, element());
      return ids.get(id);
    },
    querySelectorAll(selector) {
      assert.equal(selector, chapter==="08"?"button[data-isa]":"button[data-hazard]");
      return buttons;
    }
  };
  const html = read(chapter + ".html");
  const js = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)][0][1];
  runInNewContext(js, { document, Number, Math, Array });
  return {ids, buttons};
}
test("chapter 08 control selects srcA and keeps aria-pressed in sync", () => {
  const {ids,buttons} = run("08", {}, 4);
  buttons[2].trigger("click");
  assert.equal(ids.get("isa-choice").textContent,"srcA = %rsp");
  assert.match(ids.get("isa-explain").textContent,/ret/);
  assert.equal(buttons[2].getAttribute("aria-pressed"),"true");
  assert.equal(buttons[0].getAttribute("aria-pressed"),"false");
  buttons[3].trigger("click");
  assert.equal(ids.get("isa-choice").textContent,"srcA = RNONE");
});
test("chapter 09 speedup model and load-use result", () => {
  const {ids,buttons} = run("09", {"pipeline-n":"8"},3);
  assert.equal(ids.get("pipeline-speedup").textContent,"3.03×");
  assert.equal(ids.get("pipeline-seq").textContent,"8000 ps");
  assert.equal(ids.get("pipeline-pipe").textContent,"2640 ps");
  ids.get("pipeline-n").value="1";ids.get("pipeline-n").trigger("input");
  assert.equal(ids.get("pipeline-speedup").textContent,"0.91×");
  buttons[2].trigger("click");
  assert.match(ids.get("hazard-result").textContent,/1 个气泡/);
});
test("chapter 10 CPE lower bound responds to independent chain count", () => {
  const {ids} = run("10",{"cpe-l":"4","cpe-k":"1","cpe-r":"2"},0);
  assert.equal(ids.get("cpe-output").textContent,"4.00");
  ids.get("cpe-k").value="4";ids.get("cpe-k").trigger("input");
  assert.equal(ids.get("cpe-output").textContent,"1.00");
  ids.get("cpe-k").value="8";ids.get("cpe-l").value="1";
  ids.get("cpe-l").trigger("input");
  assert.equal(ids.get("cpe-output").textContent,"0.50");
  assert.match(ids.get("cpe-reason").textContent,/吞吐/);
});
test("standalone source examples run without invented benchmark results", () => {
  assert.match(execFileSync("python3",[join(root,"examples/olah-ch08-encoding.py")],{encoding:"utf8"}),/y86-encoding=ok/);
  assert.match(execFileSync("python3",[join(root,"examples/olah-ch09-pipeline.py")],{encoding:"utf8"}),/pipeline-schedule=ok/);
  const out = mkdtempSync(join(tmpdir(),"csapp-ch10-"));
  try {
    const bin = join(out,"sum");
    execFileSync(process.env.CC || "cc",["-std=c11","-Wall","-Wextra","-Werror","-pedantic","-O2",join(root,"examples/olah-ch10-performance.c"),"-o",bin]);
    const printed = execFileSync(bin,["10000"],{encoding:"utf8"}).trim();
    const m = printed.match(/^sum1=([^ ]+) sum4=(.+)$/);
    assert.ok(m,printed);
    const a=Number(m[1]),b=Number(m[2]);
    assert.ok(Number.isFinite(a) && Number.isFinite(b));
    assert.ok(Math.abs(a-b) <= 1e-8 * Math.max(1,Math.abs(a),Math.abs(b)));
  } finally { rmSync(out,{recursive:true,force:true}); }
});
