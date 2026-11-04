import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, relative, isAbsolute } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const manifest = JSON.parse(readFileSync(resolve(root, 'courses.json'), 'utf8'));
const htmlFiles = ['index.html', ...manifest.chapters.map((c) => c.file)];
const errors = [];

for (const file of htmlFiles) {
  const contents = readFileSync(resolve(root, file), 'utf8');
  for (const match of contents.matchAll(/\b(?:href|src)\s*=\s*["']([^"']+)["']/g)) {
    const link = match[1].trim();
    if (/^javascript:/i.test(link)) {
      errors.push(file + ': forbidden JavaScript URL ' + link);
      continue;
    }
    if (!link || link.startsWith('#') || /^(https?:|mailto:|data:|tel:)/i.test(link)) continue;
    const decoded = decodeURIComponent(link.split(/[?#]/, 1)[0]);
    if (!decoded || decoded.startsWith('/')) {
      errors.push(file + ': unsupported absolute path ' + link);
      continue;
    }
    const target = resolve(root, dirname(file), decoded);
    const outside = relative(root, target).startsWith('..') || isAbsolute(relative(root, target));
    if (outside || !existsSync(target)) errors.push(file + ': broken local link ' + link);
  }
}
if (errors.length) {
  console.error('Link validation failed:\n- ' + errors.join('\n- '));
  process.exitCode = 1;
} else {
  console.log('Link validation passed for ' + htmlFiles.length + ' pages');
}

