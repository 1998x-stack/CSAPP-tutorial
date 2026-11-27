import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = path => readFileSync(join(root, path), 'utf8');
const chapters = ['13', '14'];

for (const id of chapters) {
  test('chapter ' + id + ' second-round deep dive keeps section, TOC link, SVG and model', () => {
    const html = read(id + '.html');
    const svgPath = 'chapter-assets/' + id + '-deep2.svg';
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.match(html, new RegExp('id="deep-' + id + 'b"'));
    assert.match(html, new RegExp('href="#deep-' + id + 'b"'));
    assert.ok(html.includes('src="' + svgPath + '"'));
    assert.ok(html.includes('examples/deep-ch13-18-b.py ' + id + 'b'));
    assert.ok(existsSync(join(root, svgPath)));
    const asset = read(svgPath);
    for (const token of ['<svg', 'viewBox=', 'role="img"', '<title', '<desc']) {
      assert.ok(asset.includes(token), id + 'b: ' + token);
    }
    assert.match(html, /<figcaption>/);
    assert.match(html, /https:\/\/(?:gitlab\.com|sourceware\.org|man7\.org)/);
  });
}

test('second-round deterministic models execute', () => {
  const out = execFileSync('python3',
    [join(root, 'examples/deep-ch13-18-b.py'), 'all'], { encoding: 'utf8' });
  assert.deepEqual(out.trim().split(/\r?\n/), chapters.map(id => id + 'b:ok'));
});
