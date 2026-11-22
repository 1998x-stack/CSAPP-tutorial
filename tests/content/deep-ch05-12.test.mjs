import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(resolve(root, p), 'utf8');

test('05–12 retain accessible and independently illustrated causal deep dives', () => {
  for (let n = 5; n <= 12; n++) {
    const id = String(n).padStart(2,'0');
    const html = read(id+'.html');
    const asset = 'chapter-assets/'+id+'-deep.svg';
    assert.ok(html.includes('id="deep-'+id+'"'), id+' section');
    assert.ok(html.includes('href="#deep-'+id+'"'), id+' navigation');
    assert.ok(html.includes('src="'+asset+'"'), id+' figure');
    assert.ok(html.includes('href="deep-chapters.css"'), id+' stylesheet');
    assert.ok(html.includes('examples/deep-ch05-12.py '+id), id+' runnable case');
    assert.equal((html.match(/<h1\b/g) || []).length, 1, id+' h1');
    assert.ok(existsSync(resolve(root, asset)), id+' SVG');
    const svg=read(asset);
    for (const token of ['<svg','viewBox=','role="img"','<title','<desc']) {
      assert.ok(svg.includes(token), id+' '+token);
    }
  }
  assert.match(read('deep-chapters.css'), /@media\(max-width:650px\)/);
});

test('eight numerical and control-flow models execute independently', () => {
  const output=execFileSync('python3',
    [resolve(root,'examples/deep-ch05-12.py'),'all'], {encoding:'utf8'});
  assert.deepEqual(output.trim().split(/\r?\n/),
    ['05:ok','06:ok','07:ok','08:ok','09:ok','10:ok','11:ok','12:ok']);
});
