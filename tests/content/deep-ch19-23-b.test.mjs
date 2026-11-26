import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(resolve(root, p), 'utf8');

// Fourth-round deep dives: chapters 19-23 carry an external-SVG "deep-NNb" section.
const implemented = [19, 20, 21];

test('19-23 fourth-round deep dives keep section, TOC link, SVG asset and runnable case', () => {
  for (const n of implemented) {
    const id = String(n).padStart(2, '0');
    const html = read(id + '.html');
    assert.ok(html.includes('id="deep-' + id + 'b"'), id + ' section');
    assert.ok(html.includes('href="#deep-' + id + 'b"'), id + ' TOC');
    assert.ok(html.includes('examples/deep-ch19-23-b.py ' + id + 'b'), id + ' runnable case');
    assert.equal((html.match(/<h1\b/g) || []).length, 1, id + ' single H1');
    const at = html.indexOf('id="deep-' + id + 'b"');
    const section = html.slice(at, html.indexOf('</section>', at));
    const figure = section.slice(section.indexOf('<figure'), section.indexOf('</figure>'));
    for (const token of ['<svg', 'viewBox=', 'role="img"', '<title', '<desc'])
      assert.ok(figure.includes(token), id + ' inline SVG ' + token);
    assert.ok(/<figcaption>[^<]/.test(figure), id + ' nonempty figcaption');
  }
});

test('19-23 deterministic models execute', () => {
  const out = execFileSync('python3',
    [resolve(root, 'examples/deep-ch19-23-b.py'), 'all'], { encoding: 'utf8' });
  assert.deepEqual(out.trim().split(/\r?\n/),
    implemented.map(n => String(n).padStart(2, '0') + 'b:ok'));
});
