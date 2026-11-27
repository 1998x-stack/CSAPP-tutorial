import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(resolve(root, p), 'utf8');

// Fifth-round deep dives: chapters carry a "deep-NNb" section with a figure.
const implemented = [22, 23, 24, 25, 26];

test('22-28 fifth-round deep dives keep section, TOC link, figure and runnable case', () => {
  for (const n of implemented) {
    const id = String(n).padStart(2, '0');
    const html = read(id + '.html');
    assert.ok(html.includes('id="deep-' + id + 'b"'), id + ' section');
    assert.ok(html.includes('href="#deep-' + id + 'b"'), id + ' TOC');
    assert.ok(html.includes('examples/deep-ch22-28-b.py ' + id + 'b'), id + ' runnable case');
    assert.equal((html.match(/<h1\b/g) || []).length, 1, id + ' single H1');
    const at = html.indexOf('id="deep-' + id + 'b"');
    const section = html.slice(at, html.indexOf('</section>', at));
    const figure = section.slice(section.indexOf('<figure'), section.indexOf('</figure>'));
    assert.ok(figure.includes('<img') && figure.includes('.svg'), id + ' figure image');
    assert.ok(/<figcaption>[^<]/.test(figure), id + ' nonempty figcaption');
    const src = figure.match(/src="([^"]+\.svg)"/)[1];
    const svg = read(src);
    for (const token of ['viewBox=', '<title', '<desc', '</svg>'])
      assert.ok(svg.includes(token), id + ' SVG ' + token);
  }
});

test('22-28 deterministic models execute', () => {
  const out = execFileSync('python3',
    [resolve(root, 'examples/deep-ch22-28-b.py'), 'all'], { encoding: 'utf8' });
  assert.deepEqual(out.trim().split(/\r?\n/),
    implemented.map(n => String(n).padStart(2, '0') + 'b:ok'));
});
