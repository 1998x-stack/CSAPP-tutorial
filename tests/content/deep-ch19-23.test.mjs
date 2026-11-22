import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, mkdtempSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { execFileSync } from 'node:child_process';

const root=resolve(import.meta.dirname,'../..');
const read=p=>readFileSync(join(root,p),'utf8');
test('five independent causal diagrams and chapter navigation remain accessible',()=>{
  for (let n=19;n<=23;n++){
    const id=String(n), html=read(id+'.html');
    const svg='chapter-assets/'+id+'-deep.svg';
    assert.ok(html.includes('id="deep-'+id+'"'),id+' section');
    assert.ok(html.includes('href="#deep-'+id+'"'),id+' TOC');
    assert.ok(html.includes('src="'+svg+'"'),id+' figure');
    assert.ok(html.includes('deep-io-concurrency.css'),id+' CSS');
    assert.ok(html.includes('examples/deep-ch19-23-models.py '+id),id+' executable');
    assert.ok(existsSync(join(root,svg)),id+' asset');
    assert.equal((html.match(/<h1\b/g)||[]).length,1,id+' H1');
    for(const tag of ['<svg','viewBox=','<title','<desc','role="img"'])
      assert.ok(read(svg).includes(tag),id+' '+tag);
  }
});
test('five deterministic numerical and state models execute',()=>{
  const out=execFileSync('python3',[join(root,'examples/deep-ch19-23-models.py'),'all'],{encoding:'utf8'});
  assert.deepEqual(out.trim().split(/\r?\n/),
    ['19:ok','20:ok','21:ok','22:ok','23:ok']);
});
test('five independent real POSIX C paths compile and run without network access',()=>{
  const dir=mkdtempSync(join(tmpdir(),'csapp-deep-io-'));
  try {
    const bin=join(dir,'test');
    execFileSync(process.env.CC||'cc',['-std=c11','-Wall','-Wextra','-Werror','-pedantic',
       '-pthread',join(root,'examples/deep-ch19-23.c'),'-o',bin]);
    for(const mode of ['short-read','frame','readiness','mutex','queue']){
      const out=execFileSync(bin,[mode],{encoding:'utf8',timeout:8000});
      assert.equal(out.trim(),mode+'-ok');
    }
  } finally {rmSync(dir,{recursive:true,force:true});}
});
