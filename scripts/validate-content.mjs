import { readFileSync, existsSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const read = (path) => readFileSync(resolve(root, path), 'utf8')
const manifest = JSON.parse(read('courses.json'))
const errors = []
const fail = (message) => errors.push(message)

if (!Array.isArray(manifest.chapters) || manifest.chapters.length !== 28) {
  fail('expected 28 chapters in courses.json')
}
if (manifest.chapterCount !== manifest.chapters.length) {
  fail('manifest chapterCount mismatch')
}
const uniqueSlugs = new Set()
for (const [index, chapter] of manifest.chapters.entries()) {
  const num = String(index + 1).padStart(2, '0')
  if (chapter.num !== num) fail('out-of-order chapter ' + num)
  if (chapter.file !== num + '.html') fail('legacy filename mismatch ' + num)
  if (!new RegExp('^' + num + '-[a-z0-9-]+$').test(chapter.slug)) {
    fail('invalid slug at ' + num)
  }
  if (uniqueSlugs.has(chapter.slug)) fail('duplicate slug ' + chapter.slug)
  uniqueSlugs.add(chapter.slug)
  if (typeof chapter.title !== 'string' || !chapter.title.trim()) fail('missing title ' + num)
  if (!Array.isArray(chapter.topics) || chapter.topics.length < 1) fail('missing topics ' + num)
  const path = 'docs/chapters/' + chapter.slug + '.md'
  const redirectPath = 'docs/public/' + chapter.file
  if (!existsSync(resolve(root, path))) {
    fail('missing Markdown chapter ' + path)
    continue
  }
  const text = read(path)
  const title = 'title: ' + JSON.stringify(chapter.title)
  if (!text.startsWith('---\n') || !text.includes('\n' + title + '\n')) {
    fail('frontmatter title mismatch ' + path)
  }
  if (!/^# .+/m.test(text)) fail('missing H1 ' + path)
  if (!/^## .+/m.test(text)) fail('missing H2 ' + path)
  const fences = (text.match(/^\x60{3,}[^\n]*$/gm) || []).length
  if (fences < 2 || fences % 2 !== 0) fail('unpaired/missing fenced code block ' + path)
  if (/ZZCSAPPBLOCK\d+ZZ/.test(text)) fail('unresolved migration placeholder ' + path)
  if (/href=["']javascript:/i.test(text)) fail('JavaScript URL ' + path)
  if (!existsSync(resolve(root, redirectPath))) {
    fail('missing legacy redirect ' + redirectPath)
  } else if (!read(redirectPath).includes('./chapters/' + chapter.slug + '.html')) {
    fail('redirect destination incorrect ' + redirectPath)
  }
}
const actual = readdirSync(resolve(root, 'docs/chapters')).filter((name) => /^\d\d-.*\.md$/.test(name))
if (actual.length !== manifest.chapters.length) fail('orphan/missing Markdown chapters')
if (!read('docs/.vitepress/config.ts').includes("courseManifest from '../../courses.json'")) fail('config not linked to manifest')
if (!read('docs/index.md').includes('/chapters/')) fail('homepage has no chapter entry')
if (errors.length) {
  console.error('Content validation failed:\n- ' + errors.join('\n- '))
  process.exitCode = 1
} else {
  console.log('Validated 28 Markdown chapters, metadata, code fences and legacy redirects')
}

