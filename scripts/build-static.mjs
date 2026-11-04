import { cpSync, mkdirSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const destination = resolve(root, 'dist');
const manifest = JSON.parse(readFileSync(resolve(root, 'courses.json'), 'utf8'));
const files = ['index.html', 'theme.css', 'courses.json', ...manifest.chapters.map((x) => x.file)];
rmSync(destination, { recursive: true, force: true });
mkdirSync(destination, { recursive: true });
for (const file of files) {
  if (!/^(?:index\.html|theme\.css|courses\.json|\d{2}\.html)$/.test(file)) {
    throw new Error('unexpected build input: ' + file);
  }
  if (!existsSync(resolve(root, file))) throw new Error('missing build input: ' + file);
  cpSync(resolve(root, file), resolve(destination, file));
}
console.log('Built static site with ' + files.length + ' files at dist/');

