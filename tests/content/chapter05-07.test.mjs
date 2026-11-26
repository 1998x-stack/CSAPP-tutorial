import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

const root = resolve(import.meta.dirname, '../..');
const read = (p) => readFileSync(resolve(root, p), 'utf8');
const html = Object.fromEntries(['05','06','07'].map(n => [n, read(n + '.html')]));

for (const n of ['05','06','07']) {
  test('chapter ' + n + ' has accessible article, independent figures and traceable evidence', () => {
    const page = html[n];
    assert.match(page, /<html lang="zh-CN">/);
    assert.equal((page.match(/<h1\b/g) || []).length, 1);
    assert.match(page, /<main\b[^>]*id="main"/);
    assert.match(page, /<article class="olah-lesson">/);
    assert.match(page, /<nav class="reading-map"/);
    assert.match(page, /<details class="mobile-chapters"/);
    assert.ok((page.match(/<h2\b[^>]*>/g) || []).length >= 5);
    assert.match(page, /href="index.html"/);
    assert.match(page, /href="olah-ch05-07.css"/);
    assert.ok((page.match(/role="status" aria-live="polite"/g) || []).length >= 1);
    assert.equal((page.match(/<figcaption\b/g) || []).length, { '05': 4, '06': 4, '07': 3 }[n]);
    const images = [...page.matchAll(/<img src="(assets\/chapters\/[^"]+\.svg)"/g)];
    assert.equal(images.length, 2);
    for (const [, filename] of images) {
      assert.ok(existsSync(resolve(root, filename)), filename + ' missing');
      const svg = read(filename);
      for (const tag of ['<svg','viewBox=','role="img"','<title','<desc']) {
        assert.ok(svg.includes(tag), filename + ' missing ' + tag);
      }
    }
    const evidence = JSON.parse(read('docs/evidence/' + n + '.json'));
    assert.ok(evidence.claims.length >= 4);
    assert.equal(evidence.figures.length, 2);
    assert.ok(evidence.claims.every(x => x.claim && x.sources?.every(s => s.url && s.locator)));
    assert.equal((page.match(/<script>/g) || []).length, 1);
    assert.doesNotMatch(page, /<script[^>]+src=["']https?:/i);
  });
}

function element(value = '') {
  const handlers = new Map();
  return {
    value: String(value), textContent: '',
    addEventListener(name, fn) { handlers.set(name, fn); },
    dispatch(name) { assert.ok(handlers.has(name)); handlers.get(name)(); }
  };
}
function runWidget(page, elements) {
  const scripts = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  runInNewContext(scripts[0][1], {
    document: { querySelector(id) { assert.ok(elements[id], id); return elements[id]; } },
    Number, String
  }, { timeout: 1000 });
}

test('signed-vs-unsigned widget changes interpretation of identical 4-bit values', () => {
  const els = {
    '#signed-x': element(-1),
    '#signed-x-label': element(),
    '#signed-output': element()
  };
  runWidget(html['05'], els);
  assert.match(els['#signed-output'].textContent, /有符号 -1 < 1 = true；无符号 15 < 1 = false/);
  els['#signed-x'].value = '7';
  els['#signed-x'].dispatch('input');
  assert.match(els['#signed-output'].textContent, /有符号 7 < 1 = false；无符号 7 < 1 = false/);
});

test('recursion widget counts calls and factorial return values', () => {
  const els = {
    '#factorial-n': element(3),
    '#factorial-n-label': element(),
    '#factorial-output': element()
  };
  runWidget(html['06'], els);
  assert.match(els['#factorial-output'].textContent, /返回：6。共 3 层/);
  els['#factorial-n'].value = '0';
  els['#factorial-n'].dispatch('input');
  assert.match(els['#factorial-output'].textContent, /factorial\(0\).*返回：1。共 1 层/);
  els['#factorial-n'].value = '6';
  els['#factorial-n'].dispatch('input');
  assert.match(els['#factorial-output'].textContent, /返回：720。共 6 层/);
});

test('row-major widget computes valid byte offsets', () => {
  const els = {
    '#row-index': element(2),
    '#col-index': element(1),
    '#row-index-label': element(),
    '#col-index-label': element(),
    '#matrix-output': element()
  };
  runWidget(html['07'], els);
  assert.match(els['#matrix-output'].textContent, /36 字节/);
  els['#row-index'].value = '2';
  els['#col-index'].value = '3';
  els['#col-index'].dispatch('input');
  assert.match(els['#matrix-output'].textContent, /44 字节/);
  els['#row-index'].value = '0';
  els['#col-index'].value = '0';
  els['#row-index'].dispatch('input');
  assert.match(els['#matrix-output'].textContent, /0 字节/);
});

for (const [n, basename, expected] of [
  ['05', 'olah-ch05-control', 'flow-examples=ok'],
  ['06', 'olah-ch06-procedures', 'procedure-examples=ok'],
  ['07', 'olah-ch07-layout', 'layout-examples=ok']
]) {
  test('chapter ' + n + ' C example compiles and passes assertions', () => {
    const work = mkdtempSync(join(tmpdir(), 'csapp-ch' + n + '-'));
    try {
      const source = resolve(root, 'examples', basename + '.c');
      const exe = join(work, basename);
      const compile = spawnSync(process.env.CC || 'cc',
        ['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2',source,'-o',exe],
        { encoding:'utf8', timeout:20000 });
      assert.equal(compile.status, 0, compile.stderr || compile.error?.message);
      const args = n === '07' ? ['a-runtime-string-longer-than-eight'] : [];
      const run = spawnSync(exe, args, { encoding:'utf8', timeout:10000 });
      assert.equal(run.status, 0, run.stderr || run.error?.message);
      assert.match(run.stdout, new RegExp(expected));
    } finally { rmSync(work, { recursive: true, force: true }); }
  });
}
