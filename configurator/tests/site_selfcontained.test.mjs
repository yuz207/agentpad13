/**
 * site_selfcontained.test.mjs — the published page must make ZERO external
 * requests. Walks the whole served tree and fails on any absolute http(s)
 * reference in site source, and on any loader/import/fetch pointed at a host
 * inside the vendored three.js build.
 */

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, extname } from 'node:path';
import { suite, ok, eq, SITE } from './site_harness.mjs';

const S = suite('site_selfcontained');

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
}

const files = walk(SITE);
const isVendor = (p) => relative(SITE, p).startsWith('vendor');
const isDoc = (p) => extname(p) === '.md';
const isBinary = (p) => ['.glb', '.png', '.jpg', '.woff', '.woff2', '.ttf'].includes(extname(p));

S.test('site source contains no absolute http(s) URL', () => {
  const hits = [];
  for (const p of files) {
    if (isVendor(p) || isDoc(p) || isBinary(p)) continue;
    const text = readFileSync(p, 'utf8');
    for (const m of text.matchAll(/https?:\/\/[^\s"'`)]+/g)) hits.push(`${relative(SITE, p)}: ${m[0]}`);
  }
  eq(hits.length, 0, `external references found:\n        ${hits.join('\n        ')}`);
});

S.test('index.html loads nothing off-host: no src/href to another origin', () => {
  const html = readFileSync(join(SITE, 'index.html'), 'utf8');
  for (const m of html.matchAll(/(?:src|href)\s*=\s*"([^"]+)"/g)) {
    const url = m[1];
    ok(!/^[a-z]+:\/\//i.test(url) && !url.startsWith('//'), `off-host asset: ${url}`);
  }
});

S.test('the import map resolves three from the vendored copy', () => {
  const html = readFileSync(join(SITE, 'index.html'), 'utf8');
  const m = html.match(/<script type="importmap">([\s\S]*?)<\/script>/);
  ok(m, 'an import map is required so the addons can say "three"');
  const map = JSON.parse(m[1]);
  ok(map.imports.three.startsWith('./vendor/three/'), 'three must resolve locally');
  ok(map.imports['three/addons/'].startsWith('./vendor/three/'), 'addons must resolve locally');
});

/** Strip comments so three's own doc comments (which cite example CDN URLs)
 *  do not masquerade as runtime references. `[^:]` keeps `https://` in code. */
const stripComments = (src) =>
  src.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1');

S.test('vendored three.js never imports or fetches from a host', () => {
  const bad = [];
  for (const p of files) {
    if (!isVendor(p) || extname(p) !== '.js') continue;
    const text = stripComments(readFileSync(p, 'utf8'));
    for (const re of [/from\s*["']https?:/g, /import\s*\(\s*["']https?:/g, /fetch\s*\(\s*["']https?:/g,
                      /importScripts\s*\(\s*["']https?:/g]) {
      for (const m of text.matchAll(re)) bad.push(`${relative(SITE, p)}: ${m[0]}`);
    }
  }
  eq(bad.length, 0, `vendored code reaches out:\n        ${bad.join('\n        ')}`);
});

S.test('the vendored three.js build is pinned and hashed in VENDORED.md', () => {
  const doc = readFileSync(join(SITE, 'vendor', 'three', 'VENDORED.md'), 'utf8');
  ok(/0\.185\.1/.test(doc), 'the version must be pinned in the doc');
  const hashes = [...doc.matchAll(/`([0-9a-f]{64})`/g)].map((m) => m[1]);
  ok(hashes.length >= 8, `expected the tarball + per-file sha256 table, found ${hashes.length}`);
  ok(/registry\.npmjs\.org/.test(doc), 'the source URL must be recorded');
});

S.test('no font, style or worker is pulled from a CDN', () => {
  const css = readFileSync(join(SITE, 'styles.css'), 'utf8');
  ok(!/@import\s+url\(\s*["']?https?:/.test(css), 'no remote @import');
  ok(!/src:\s*url\(\s*["']?https?:/.test(css), 'no remote font file');
});

S.run();
