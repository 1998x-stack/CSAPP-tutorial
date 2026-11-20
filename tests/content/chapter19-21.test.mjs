import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { spawnSync } from 'node:child_process';
const root = resolve(import.meta.dirname, '../..');
const read = p => readFileSync(join(root, p), 'utf8');
const decode = s => s.replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&amp;', '&');
const snippets = n => [...read(n + '.html').matchAll(/<pre><code>([\s\S]*?)<\/code><\/pre>/g)].map(x => decode(x[1]));
function run(command, args, cwd) {
  const p = spawnSync(command, args, { cwd, encoding: 'utf8', timeout: 30000 });
  assert.equal(p.status, 0, command + ': ' + p.stderr);
  return p.stdout;
}
test('chapter 19–21 reading structure, SVG and source ledger', () => {
  for (const n of [19, 20, 21]) {
    const html = read(n + '.html');
    assert.equal((html.match(/<h1>/g) || []).length, 1);
    assert.ok((html.match(/<h2>/g) || []).length >= 6);
    assert.match(html, /id="chapter-main"/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /href="olah-chapters.css"/);
    const assets = [...html.matchAll(/<img src="(chapter-assets\/[^"]+\.svg)"/g)].map(m => m[1]);
    assert.equal(assets.length, 2);
    for (const asset of assets) {
      assert.ok(existsSync(join(root, asset)), asset);
      assert.match(read(asset), /<svg[^>]+viewBox=/);
      assert.match(read(asset), /<title[^>]*>/);
      assert.match(read(asset), /<desc[^>]*>/);
    }
    assert.ok(JSON.parse(read('evidence/' + n + '.json')).claims.length >= 3);
  }
});
test('standalone POSIX examples compile and execute', () => {
  const folder = mkdtempSync(join(tmpdir(), 'csapp-19-21-'));
  try {
    for (const x of [[19,0,'copy'],[20,2,'resolve'],[21,1,'cgi'],[21,2,'select-demo']]) {
      const source = snippets(x[0])[x[1]];
      assert.match(source, /int main/);
      writeFileSync(join(folder, x[2] + '.c'), source);
      run('cc', ['-std=c11','-Wall','-Wextra','-pedantic',x[2]+'.c','-o',x[2]], folder);
    }
    writeFileSync(join(folder, 'input.bin'), 'HELLO CSAPP\n');
    run('./copy', ['input.bin','output.bin'], folder);
    assert.equal(readFileSync(join(folder, 'output.bin'), 'utf8'), 'HELLO CSAPP\n');
    assert.match(run('./resolve', ['localhost'], folder), /:80/);
    assert.match(run('./cgi', [], folder), /Content-Type: text\/html; charset=UTF-8/);
    assert.match(run('./select-demo', [], folder), /a ready: 0, b ready: 1/);
  } finally { rmSync(folder, { recursive: true, force: true }); }
});
