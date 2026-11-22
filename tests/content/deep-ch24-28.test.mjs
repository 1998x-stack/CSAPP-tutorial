import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';

const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(join(root, p), 'utf8');

// Chapters that ship an independent deep-dive section, keyed by chapter number.
const implemented = { 24: '24-deep.svg', 25: '25-deep.svg', 26: '26-deep.svg', 27: '27-deep.svg', 28: '28-deep.svg' };

test('lab/systems deep dives keep a section, TOC link, standalone SVG and CSS', () => {
  for (const [id, svg] of Object.entries(implemented)) {
    const html = read(id + '.html');
    assert.ok(html.includes('id="deep-' + id + '"'), id + ' section');
    assert.ok(html.includes('href="#deep-' + id + '"'), id + ' TOC');
    assert.ok(html.includes('class="deep-study"'), id + ' wrapper class');
    assert.ok(html.includes('src="chapter-assets/' + svg + '"'), id + ' figure');
    assert.ok(html.includes('deep-labs.css'), id + ' CSS');
    assert.ok(existsSync(join(root, 'chapter-assets', svg)), id + ' asset');
    assert.equal((html.match(/<h1\b/g) || []).length, 1, id + ' H1');
    const svgText = read('chapter-assets/' + svg);
    for (const tag of ['<svg', 'viewBox=', '<title', '<desc', 'role="img"', '</svg>'])
      assert.ok(svgText.includes(tag), id + ' ' + tag);
  }
});

test('deterministic lab/systems models execute', () => {
  const out = execFileSync('python3', [join(root, 'examples/deep-ch24-28-models.py'), 'all'], { encoding: 'utf8' });
  assert.deepEqual(out.trim().split(/\r?\n/), Object.keys(implemented).map(n => n + ':ok'));
});

test('lab/systems evidence ledgers extend the verified claims', () => {
  for (const id of Object.keys(implemented)) {
    const ledger = JSON.parse(read('docs/evidence/' + id + '.json'));
    assert.ok(Array.isArray(ledger.claims) && ledger.claims.length >= 4, id + ' claims');
    assert.ok(ledger.claims.every(c => c.id && c.claim && c.source_url && c.locator && c.status), id + ' fields');
  }
});
