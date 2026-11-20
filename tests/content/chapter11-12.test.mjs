import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const read = (path) => readFileSync(new URL('../../' + path, import.meta.url), 'utf8');
const pages = {
  '11': {html: read('11.html'), assets: ['11-hierarchy.svg','11-locality.svg','11-ftl.svg']},
  '12': {html: read('12.html'), assets: ['12-address.svg','12-sets.svg','12-blocking.svg']}
};

for (const [chapter, page] of Object.entries(pages)) {
  test('chapter ' + chapter + ' content, evidence, SVG and navigation', () => {
    const html = page.html;
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.match(html, /<main\b[^>]*id="content"/);
    assert.match(html, /<html lang="zh-CN">/);
    assert.match(html, /aria-current="page"/);
    assert.match(html, /href="index\.html"/);
    assert.match(html, chapter === '11' ? /href="12\.html"/ : /href="13\.html"/);
    assert.equal((html.match(/<svg\b/g) || []).length, 3);
    assert.equal((html.match(/<figcaption\b/g) || []).length, 3);
    assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
    assert.ok(!html.includes('原创图解 · 单文件离线 HTML'));
    const inline = [...html.matchAll(/<svg\b[\s\S]*?<\/svg>/g)].map(m => m[0]);
    page.assets.forEach((name, i) => {
      const asset = read('docs/chapters/assets/' + name);
      assert.equal(asset.replace(/^<\?xml[^>]*\?>\s*/, '').trim(), inline[i].trim());
      assert.match(asset, /<title\b/);
      assert.match(asset, /<desc\b/);
      assert.match(asset, /viewBox="/);
      assert.match(asset, /xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
      assert.ok(!/<script\b/i.test(asset));
    });
    const evidence = JSON.parse(read('docs/evidence/' + chapter + '.json'));
    assert.ok(evidence.claims.length >= 7);
    assert.ok(evidence.claims.every(c => c.id && c.claim && c.kind && c.source_url && c.locator && c.status && c.notes));
    assert.ok(evidence.claims.every(c => ['verified','derived','illustrative','unverified'].includes(c.status)));
  });
}
function element(value = '') {
  const callbacks = {}, attrs = {};
  return {
    value, textContent: '',
    addEventListener(type, fn) { callbacks[type] = fn; },
    dispatch(type) { assert.ok(callbacks[type]); callbacks[type](); },
    setAttribute(key, val) { attrs[key] = String(val); },
    getAttribute(key) { return attrs[key] ?? null; }
  };
}
function inlineScript(html) {
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  return scripts[0][1];
}
test('chapter 11 stride widget updates substantive math and accessible output', () => {
  const ids = new Map(['stride','stride-label','used','used-detail','waste'].map(x => [x, element()]));
  ids.get('stride').value = '0';
  runInNewContext(inlineScript(pages['11'].html), {
    document: { getElementById(id) { assert.ok(ids.has(id), id); return ids.get(id); } },
    Number, Math
  });
  assert.equal(ids.get('used').textContent, '100%');
  ids.get('stride').value = '3';  // stride 8: 2 elements/line
  ids.get('stride').dispatch('input');
  assert.equal(ids.get('used').textContent, '12.50%');
  assert.equal(ids.get('waste').textContent, '56 B');
  ids.get('stride').value = '4';  // stride 16: 1 element/line
  ids.get('stride').dispatch('input');
  assert.equal(ids.get('used').textContent, '6.25%');
  assert.match(ids.get('used-detail').textContent, /1 个元素/);
});
test('chapter 12 set mapping widget tracks two ways and hit sequence', () => {
  const names = ['way0-text','way1-text','cache-result','cache-why'];
  const ids = new Map(names.map(x => [x, element()]));
  const buttons = [0,1,2,3].map(() => element());
  runInNewContext(inlineScript(pages['12'].html), {
    document: {
      getElementById(id) { assert.ok(ids.has(id), id); return ids.get(id); },
      querySelectorAll(selector) { assert.equal(selector, 'button[data-cache-step]'); return buttons; }
    }, Number, String, Array
  });
  assert.equal(ids.get('way0-text').textContent, '空');
  buttons[1].dispatch('click');
  assert.equal(ids.get('way0-text').textContent, 'tag 0');
  assert.match(ids.get('cache-result').textContent, /未命中/);
  buttons[2].dispatch('click');
  assert.equal(ids.get('way1-text').textContent, 'tag 1');
  buttons[3].dispatch('click');
  assert.match(ids.get('cache-result').textContent, /命中/);
  assert.equal(buttons[3].getAttribute('aria-pressed'), 'true');
  assert.equal(buttons[2].getAttribute('aria-pressed'), 'false');
});
