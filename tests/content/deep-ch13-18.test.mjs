import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const read = path => readFileSync(join(root, path), 'utf8');

for (let chapter = 13; chapter <= 18; chapter++) {
  test('chapter '+chapter+' preserves standalone narrative and cross-linked deep proof', () => {
    const id = String(chapter);
    const html = read(id+'.html');
    const svgPath = 'chapter-assets/'+id+'-deep.svg';
    assert.match(html, /<html lang="zh-CN">/);
    assert.equal((html.match(/<h1\b/g) || []).length, 1);
    assert.match(html, new RegExp('id="deep-'+id+'"'));
    assert.match(html, new RegExp('href="#deep-'+id+'"'));
    assert.ok(html.includes('src="'+svgPath+'"'));
    assert.ok(html.includes('href="deep-systems.css"'));
    assert.ok(html.includes('examples/deep-ch13-18-models.py '+id));
    assert.ok(existsSync(join(root,svgPath)));
    const asset = read(svgPath);
    for (const token of ['<svg', 'viewBox=', 'role="img"', '<title', '<desc']) {
      assert.ok(asset.includes(token), id+': '+token);
    }
    assert.match(html, /<figcaption>/);
    assert.match(html, /https:\/\/(?:man7\.org|www\.kernel\.org|gitlab\.com|www\.sourceware\.org)/);
  });
}

test('all six causal models pass deterministic assertions', () => {
  const out = execFileSync('python3', [join(root,'examples/deep-ch13-18-models.py'),'all'],{encoding:'utf8'});
  assert.deepEqual(out.trim().split(/\r?\n/),
    ['13:ok','14:ok','15:ok','16:ok','17:ok','18:ok']);
});

test('real POSIX fork/wait, pending signal/sigsuspend and realloc are reproducible', () => {
  const work = mkdtempSync(join(tmpdir(),'csapp-systems-'));
  try {
    const exe = join(work,'deep-posix');
    execFileSync(process.env.CC || 'cc', [
      '-std=c11','-D_POSIX_C_SOURCE=200809L','-Wall','-Wextra','-Werror','-pedantic','-O2',
      join(root,'examples/deep-ch13-18-posix.c'),'-o',exe
    ]);
    for (const [mode, expected] of [['fork','fork-ok'],['signal','signal-ok'],['realloc','realloc-ok']]) {
      const stdout = execFileSync(exe,[mode],{encoding:'utf8',timeout:5000});
      assert.equal(stdout.trim(),expected);
    }
  } finally {
    rmSync(work,{recursive:true,force:true});
  }
});

test('ELF inspection examples compile independently with no unresolved-link requirement', () => {
  const work = mkdtempSync(join(tmpdir(),'csapp-elf-'));
  try {
    const object = join(work,'reloc.o');
    const library = join(work,'libdeep.so');
    execFileSync(process.env.CC || 'cc',
      ['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O0','-c',
       join(root,'examples/deep-ch13-18-reloc.c'),'-o',object]);
    execFileSync(process.env.CC || 'cc',
      ['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O0','-fPIC','-shared',
       join(root,'examples/deep-ch13-18-shared.c'),'-o',library]);
    assert.ok(existsSync(object) && existsSync(library));
    if (process.platform === 'linux') {
      const readelf = execFileSync('readelf',['-rW',object],{encoding:'utf8'});
      assert.match(readelf,/plus_one/);
      assert.match(readelf,/R_X86_64_(?:PLT32|PC32)/);
      assert.match(execFileSync('readelf',['-h',library],{encoding:'utf8'}),/DYN/);
    }
  } finally { rmSync(work,{recursive:true,force:true}); }
});
