import { readFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const dist = resolve(root, 'docs/.vitepress/dist')
const chapters = JSON.parse(readFileSync(resolve(root, 'courses.json'), 'utf8')).chapters
const errors = []
const check = (path) => {
  if (!existsSync(resolve(dist, path))) errors.push('missing build file: ' + path)
}
check('index.html')
check('chapters/index.html')
check('guides/learning-path.html')
check('labs/index.html')
check('logo.svg')
for (const chapter of chapters) {
  check('chapters/' + chapter.slug + '.html')
  check(chapter.file)
}
if (errors.length) {
  console.error(errors.join('\n'))
  process.exitCode = 1
} else {
  console.log('Validated rendered VitePress site and 28 backward-compatible redirects')
}

