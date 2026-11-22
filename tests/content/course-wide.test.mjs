import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
const root = new URL('../../', import.meta.url);
const read = name => readFileSync(new URL(name, root), 'utf8');
const chapters = JSON.parse(read('courses.json')).chapters;
test('28 standalone HTML pages expose accessible metadata and grounded cross-links', () => {
  assert.equal(chapters.length, 28);
  const files = new Set(chapters.map(x => x.file));
  for (const chapter of chapters) {
    const html = read(chapter.file);
    const num = chapter.num;
    assert.match(html, /<meta name="description" content="[^"]+">/, chapter.file);
    assert.ok(html.includes('href="https://1998x-stack.github.io/CSAPP-tutorial/' + num + '.html"'), chapter.file + ' canonical');
    assert.match(html, /name="viewport" content="width=device-width, initial-scale=1"/, chapter.file);
    assert.doesNotMatch(html, /(?:maximum-scale|user-scalable\s*=\s*no)/i, chapter.file);
    assert.match(html, /href="course-improvements\.css"/, chapter.file);
    assert.equal((html.match(/<h1\b/g) || []).length, 1, chapter.file + ' h1');
    assert.equal((html.match(/class="concept-bridge"/g) || []).length, 1, chapter.file + ' bridge');
    const bridge = html.match(/<aside class="concept-bridge"[\s\S]*?<\/aside>/);
    assert.ok(bridge, chapter.file + ' bridge section');
    const linked = [...bridge[0].matchAll(/href="(\d{2}\.html)"/g)].map(m => m[1]);
    assert.equal(linked.length, 2, chapter.file + ' two cross-chapter questions');
    assert.ok(linked.every(x => files.has(x) && x !== chapter.file), chapter.file + ' valid links');
    for (const href of html.matchAll(/href="#([^"]+)"/g)) {
      const anchor = href[1];
      assert.ok(html.includes('id="' + anchor + '"') || html.includes("id='" + anchor + "'"), chapter.file + ': broken fragment #' + anchor);
    }
  }
});
test('homepage provides independent, static, contextual reading paths', () => {
  const html = read('index.html');
  assert.match(html, /id="traces"/);
  assert.equal((html.match(/class="trace-card"/g) || []).length, 3);
  assert.equal((html.match(/class="trace-steps"/g) || []).length, 3);
  assert.match(html, /href="#traces"/);
  assert.match(read('home.css'), /\.trace-grid/);
});
