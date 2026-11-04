import { readFileSync, existsSync } from 'node:fs'
import { resolve, dirname, extname } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const docs = resolve(root, 'docs')
const read = (path) => readFileSync(resolve(root, path), 'utf8')
const manifest = JSON.parse(read('courses.json'))
const files = ['docs/index.md', 'docs/chapters/index.md', 'docs/labs/index.md',
  'docs/guides/learning-path.md', 'docs/guides/content-style.md',
  ...manifest.chapters.map((c) => 'docs/chapters/' + c.slug + '.md')]
const errors = []

for (const file of files) {
  const text = read(file)
  const withoutCode = text.replace(/^\x60{3,}[\s\S]*?^\x60{3,}[ \t]*$/gm, '')
  for (const match of withoutCode.matchAll(/!?\[[^\]]*]\(([^)\s]+)(?:\s+["'][^"']+["'])?\)/g)) {
    const uri = match[1]
    if (/^(?:https?:\/\/|mailto:|#)/i.test(uri)) continue
    const path = decodeURIComponent(uri.split(/[?#]/, 1)[0])
    if (!path) continue
    const target = path.startsWith('/') ? resolve(docs, '.' + path) : resolve(dirname(resolve(root, file)), path)
    if (!target.startsWith(docs + '/') && target !== docs) {
      errors.push(file + ': link escapes docs/ ' + uri)
      continue
    }
    const candidates = extname(target) ? [target] : [target + '.md', resolve(target, 'index.md')]
    if (!candidates.some(existsSync)) errors.push(file + ': broken link ' + uri)
  }
}
for (const item of manifest.chapters) {
  const stub = read('docs/public/' + item.file)
  if (!stub.includes('./chapters/' + item.slug + '.html')) errors.push('broken legacy redirect: ' + item.file)
}
if (errors.length) {
  console.error('Broken internal links:\n- ' + errors.join('\n- '))
  process.exitCode = 1
} else {
  console.log('Checked internal Markdown links and 28 legacy redirects')
}

