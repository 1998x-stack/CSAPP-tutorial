import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const root = new URL('../../', import.meta.url);
const read = path => readFileSync(new URL(path, root), 'utf8');
const html = read('index.html');
const css = read('home.css');
const manifest = JSON.parse(read('courses.json'));
const linkRe = /<a class="chapter-card" href="([^"]+)" data-stage="([^"]+)" data-search="([^"]+)"/g;
const links = [...html.matchAll(linkRe)];

test('homepage includes all chapter links without requiring JavaScript', () => {
  assert.match(html, /<html lang="zh-CN">/);
  assert.match(html, /href="home\.css"/);
  assert.equal((html.match(/<h1\b/g) || []).length, 1);
  assert.equal(links.length, 28);
  assert.equal(new Set(links.map(x => x[1])).size, 28);
  assert.deepEqual(links.map(x => x[1]), manifest.chapters.map(c => c.file));
  assert.equal((html.match(/class="stage"/g) || []).length, 7);
  assert.equal(new Set(links.map(x => x[2])).size, 7);
  for (const [index, entry] of links.entries()) {
    assert.ok(entry[3].includes(manifest.chapters[index].title), 'chapter title must match manifest');
    assert.ok(entry[3].includes(manifest.chapters[index].topics[0]), 'search keywords need topics');
  }
  assert.match(html, /href="#main-content"/);
  assert.match(html, /<nav class="top-nav" aria-label=/);
  assert.match(html, /<label class="search-label" for="chapter-search">/);
  assert.match(html, /aria-live="polite"/);
  assert.match(css, /\.catalog-tools\[hidden\]/);
  assert.ok(!/<script[^>]+src=["']https?:/i.test(html));
  assert.match(html, /fetch\('courses\.json'\)/);
});

function element(value = '') {
  const events = {};
  const attrs = {};
  return {
    value, textContent:'', hidden:false, dataset:{},
    addEventListener(type, fn) {events[type] = fn;},
    fire(type, event = {}) {assert.ok(events[type], type); events[type](event);},
    setAttribute(k, v) {attrs[k] = String(v);},
    getAttribute(k) {return attrs[k] ?? null;},
    focus() {this.focused = true;},
    scrollIntoView() {this.scrolled = true;},
  };
}

test('search, stage filters, empty results and route navigation update visible chapters', () => {
  const cardNodes = links.map(([_, href, stage, search]) => ({
    hidden:false, dataset:{stage, search}, textContent:search,
    getAttribute(k) {return k === 'href' ? href : null;}
  }));
  const buttons = ['all','foundation','machine','cpu','memory','runtime','network','practice'].map(key => {
    const node = element();
    node.dataset.filter = key;
    return node;
  });
  const routes = ['foundation','machine','cpu','memory','runtime','network','practice'].map(key => {
    const node = element();
    node.dataset.route = key;
    return node;
  });
  const ids = new Map(['chapter-search','catalog-tools','chapter-filters','chapter-count','empty-state','catalog'].map(key => [key,element()]));
  ids.get('catalog-tools').hidden = true;
  ids.get('chapter-filters').hidden = true;
  ids.get('empty-state').hidden = true;
  ids.get('chapter-filters').querySelectorAll = selector => {
    assert.equal(selector, 'button[data-filter]');
    return buttons;
  };
  const source = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(source.length, 1);
  runInNewContext(source[0][1], {
    document: {
      documentElement:{dataset:{}},
      querySelectorAll(selector) {
        if(selector === '.chapter-card') return cardNodes;
        if(selector === 'a[data-route]') return routes;
        throw new Error(selector);
      },
      getElementById(id) {assert.ok(ids.has(id), id);return ids.get(id);}
    },
    fetch() { return Promise.reject(new Error('offline')); },
  });
  assert.equal(ids.get('catalog-tools').hidden, false);
  assert.equal(ids.get('chapter-filters').hidden, false);
  assert.equal(cardNodes.filter(c => !c.hidden).length, 28);
  buttons[4].fire('click');
  assert.equal(buttons[4].getAttribute('aria-pressed'), 'true');
  assert.equal(cardNodes.filter(c => !c.hidden).length, 2);
  ids.get('chapter-search').value = 'Cache';
  ids.get('chapter-search').fire('input');
  assert.match(ids.get('chapter-count').textContent, /显示 1 \/ 28/);
  ids.get('chapter-search').value = '没有这个知识点';
  ids.get('chapter-search').fire('input');
  assert.equal(ids.get('empty-state').hidden, false);
  ids.get('chapter-search').fire('keydown', {key:'Escape'});
  assert.equal(ids.get('chapter-search').value, '');
  assert.equal(cardNodes.filter(c => !c.hidden).length, 2);
  routes[6].fire('click', {preventDefault(){}});
  assert.equal(cardNodes.filter(c => !c.hidden).length, 5);
  assert.equal(ids.get('catalog').scrolled, true);
  assert.equal(ids.get('chapter-search').focused, true);
});
