import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(resolve(root, p), 'utf8');

// Chapters 01-04 carry an inline-SVG deep-dive section and a runnable model.
const implemented = [2, 3, 4];

test('01-04 deep dives keep a section, TOC link, inline SVG and CSS', () => {
  for (const n of implemented) {
    const id = String(n).padStart(2, '0');
    const html = read(id + '.html');
    assert.ok(html.includes('id="deep-' + id + '"'), id + ' section');
    assert.ok(html.includes('href="#deep-' + id + '"'), id + ' TOC');
    assert.ok(html.includes('class="deep-study"'), id + ' wrapper class');
    assert.ok(html.includes('href="deep-chapters.css"'), id + ' CSS link');
    assert.ok(html.includes('examples/deep-ch01-04.py ' + id), id + ' runnable case');
    assert.equal((html.match(/<h1\b/g) || []).length, 1, id + ' single H1');
    // The deep-dive figure renders inline so validate.py sees a real SVG.
    const section = html.slice(html.indexOf('id="deep-' + id + '"'));
    const figure = section.slice(section.indexOf('<figure'), section.indexOf('</figure>'));
    for (const token of ['<svg', 'viewBox=', 'role="img"', '<title', '<desc'])
      assert.ok(figure.includes(token), id + ' inline SVG ' + token);
  }
});

test('01-04 deterministic models execute', () => {
  const out = execFileSync('python3',
    [resolve(root, 'examples/deep-ch01-04.py'), 'all'], { encoding: 'utf8' });
  assert.deepEqual(out.trim().split(/\r?\n/),
    implemented.map(n => String(n).padStart(2, '0') + ':ok'));
});
