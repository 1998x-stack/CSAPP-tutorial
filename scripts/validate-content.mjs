import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const read = (path) => readFileSync(resolve(root, path), 'utf8');
const manifest = JSON.parse(read('courses.json'));
const errors = [];
const fail = (message) => errors.push(message);

assert.equal(Array.isArray(manifest.chapters), true, 'courses.json chapters must be an array');
if (manifest.chapterCount !== manifest.chapters.length) fail('chapterCount differs from chapters.length');
if (manifest.chapters.length !== 28) fail('expected 28 chapters');

const nums = new Set();
const files = new Set();
for (const [index, chapter] of manifest.chapters.entries()) {
  const num = String(index + 1).padStart(2, '0');
  if (chapter.num !== num) fail('chapter order/number mismatch: ' + num);
  if (nums.has(chapter.num)) fail('duplicate number: ' + chapter.num);
  nums.add(chapter.num);
  if (!/^\d{2}\.html$/.test(chapter.file)) fail('unsafe/invalid path: ' + chapter.file);
  if (files.has(chapter.file)) fail('duplicate chapter path: ' + chapter.file);
  files.add(chapter.file);
  if (chapter.file !== num + '.html') fail('unexpected filename: ' + chapter.file);
  if (!chapter.title || !Array.isArray(chapter.topics) || chapter.topics.length === 0) {
    fail('missing title/topics: ' + num);
  }
  if (!existsSync(resolve(root, chapter.file))) {
    fail('missing file: ' + chapter.file);
    continue;
  }
  const html = read(chapter.file);
  if (!html.includes('<html lang="zh-CN">')) fail('missing lang: ' + chapter.file);
  if (!/<title>[^<]+<\/title>/.test(html)) fail('missing title: ' + chapter.file);
  if (!/<h2>[^<]+<\/h2>/.test(html)) fail('missing article heading: ' + chapter.file);
  if (!html.includes('href="index.html"')) fail('missing index navigation: ' + chapter.file);
  if (/href=["']javascript:/i.test(html)) fail('inactive javascript link: ' + chapter.file);
  if (index > 0 && !html.includes('href="' + String(index).padStart(2, '0') + '.html"')) {
    fail('missing previous chapter link: ' + chapter.file);
  }
  if (index < 27 && !html.includes('href="' + String(index + 2).padStart(2, '0') + '.html"')) {
    fail('missing next chapter link: ' + chapter.file);
  }
}
if (read('theme.css').trimStart().startsWith('<!--')) fail('theme.css has an HTML comment instead of CSS comment');
if (!read('index.html').includes("fetch('courses.json')")) fail('index is disconnected from courses.json');
if (errors.length) {
  console.error('Content validation failed:\n- ' + errors.join('\n- '));
  process.exitCode = 1;
} else {
  console.log('Content validated: 28 ordered chapters, links and metadata');
}

