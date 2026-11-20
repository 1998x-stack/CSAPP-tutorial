import { cpSync, mkdirSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { resolve, relative, dirname, isAbsolute } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const destination = resolve(root, 'dist');
const manifest = JSON.parse(readFileSync(resolve(root, 'courses.json'), 'utf8'));
const pages = ['index.html', ...manifest.chapters.map((x) => x.file)];
const files = new Set([...pages, 'theme.css', 'olah-chapters.css', 'chapter-olah.css', 'courses.json']);

/* Copy chapter-local CSS, figures and scripts as well as HTML entrypoints.
   This keeps independently authored SVGs from disappearing during Pages deploy. */
for (const page of pages) {
  const contents = readFileSync(resolve(root, page), 'utf8');
  for (const match of contents.matchAll(/\b(?:href|src)\s*=\s*["']([^"']+)["']/g)) {
    const raw = match[1].trim();
    if (!raw || raw.startsWith('#') || /^(?:https?:|mailto:|tel:|data:)/i.test(raw)) continue;
    const name = decodeURIComponent(raw.split(/[?#]/, 1)[0]);
    if (!/\.(?:css|svg|png|jpe?g|webp|js)$/i.test(name)) continue;
    const absolute = resolve(root, dirname(page), name);
    const target = relative(root, absolute);
    if (isAbsolute(target) || target === '..' || target.startsWith('../')) {
      throw new Error('asset escapes root: ' + raw);
    }
    if (!existsSync(absolute)) throw new Error('missing page asset: ' + page + ': ' + name);
    files.add(target);
  }
}

rmSync(destination, { recursive: true, force: true });
mkdirSync(destination, { recursive: true });
for (const file of files) {
  if (!/^(?:index\.html|theme\.css|courses\.json|\d{2}\.html|[a-zA-Z0-9_./-]+\.(?:css|svg|png|jpe?g|webp|js))$/.test(file)) {
    throw new Error('unexpected build input: ' + file);
  }
  if (!existsSync(resolve(root, file))) throw new Error('missing build input: ' + file);
  mkdirSync(dirname(resolve(destination, file)), { recursive: true });
  cpSync(resolve(root, file), resolve(destination, file));
}
if (existsSync(resolve(root, 'chapter-assets'))) {
  cpSync(resolve(root, 'chapter-assets'), resolve(destination, 'chapter-assets'), { recursive: true });
}
console.log('Built static site with ' + files.size + ' files at dist/');
