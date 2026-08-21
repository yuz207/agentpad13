/**
 * site_text_audit.mjs — the style-mandate audit.
 *
 *   node configurator/tests/site_text_audit.mjs <dom-dump.html>
 *
 * The owner's mandate: "Let's keep this clean, minimal, no useless chrome or
 * text like eyebrows or mustaches." So the ONLY text allowed to render is:
 *
 *   1. a group label   — one word (plus the "LED band" master toggle)
 *   2. an option VALUE — the text a control shows FOR its own value, and
 *      nothing else. Three control shapes carry one:
 *        .seg     a segmented cell    ("yes", "5.4", "tented ring")
 *        .pick    a colour NAME, on the BUTTON only
 *                 (round 3: the owner asked for "current color and you click
 *                  to select from a drop down", so the name renders now.
 *                  round 4 turned the open panel into a GRID of swatches —
 *                  "Then you can have more colors" — and a swatch carries no
 *                  text at all: its name is a title/aria-label, so a 56-colour
 *                  palette adds exactly one rendered string to the page)
 *        .checks  a checkbox's own word ("caps", "translucent", "lit") —
 *                 identical boxes in a list, never sized per item
 *   3. build-sheet content — everything inside #sheet, including the three
 *      outcome-changing notes the spec allows
 *
 * Anything else — an eyebrow, a subtitle, a "Choose your…", a helper
 * paragraph, a badge — is a violation. The correct violation count is 0.
 *
 * The dump is produced from the running page, e.g.
 *   chrome --headless --dump-dom URL > dom.html
 * so this audits what actually renders, not what the source hopes renders.
 */

import { readFileSync } from 'node:fs';

/* 'Lighting' is round 4's own section — "Maybe lighting becomes its own
   section" — and like every other label it is ONE word. */
const ALLOWED_LABELS = new Set(['LED band', 'Lighting', 'Board', 'Plate', 'Band', 'Tray', 'Base', 'Show', 'Caps', 'Switches', 'Toppers']);

/** Minimal HTML walker: enough for the markup this site emits. */
function textNodes(html) {
  const body = html.includes('<body') ? html.slice(html.indexOf('<body')) : html;
  const clean = body
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '');
  const out = [];
  const stack = [];
  const re = /<(\/?)([a-zA-Z][\w-]*)((?:"[^"]*"|'[^']*'|[^>"'])*)(\/?)>/g;
  let last = 0, m;
  const push = (text) => {
    const t = text.replace(/\s+/g, ' ').trim();
    if (!t) return;
    out.push({ text: t, stack: stack.slice() });
  };
  while ((m = re.exec(clean))) {
    push(clean.slice(last, m.index));
    last = re.lastIndex;
    const [, closing, tag, attrs, selfClose] = m;
    if (closing) {
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].tag === tag) { stack.length = i; break; }
      }
    } else if (!selfClose && !/^(br|img|input|meta|link|hr|source)$/i.test(tag)) {
      stack.push({
        tag,
        id: (attrs.match(/\bid="([^"]*)"/) || [])[1] || '',
        cls: (attrs.match(/\bclass="([^"]*)"/) || [])[1] || '',
        hidden: /\bhidden\b/.test(attrs),
      });
    }
  }
  push(clean.slice(last));
  return out;
}

/** The three control shapes, and where inside each one a value may render. */
const VALUE_IN = [
  ['seg', (n) => n.stack.at(-1).tag === 'button'],          // a segmented cell
  ['pick', () => true],                                     // the colour name, button + listbox
  ['checks', () => true],                                   // a checkbox's own word
];

function classify(node) {
  const has = (cls) => node.stack.some((e) => e.cls.split(/\s+/).includes(cls));
  const inside = (pred) => node.stack.some(pred);
  if (inside((e) => e.hidden)) return 'not-rendered (hidden control)';
  if (inside((e) => e.id === 'sheet')) return 'sheet content';
  if (has('label')) {
    return ALLOWED_LABELS.has(node.text) ? 'group label' : 'VIOLATION: label not in the allowed set';
  }
  for (const [cls, where] of VALUE_IN) if (has(cls) && where(node)) return 'option value';
  return 'VIOLATION: text that is not a label, a value or sheet content';
}

const file = process.argv[2];
if (!file) { console.error('usage: node site_text_audit.mjs <dom-dump.html>'); process.exit(2); }

const nodes = textNodes(readFileSync(file, 'utf8'));
const buckets = new Map();
for (const n of nodes) {
  const k = classify(n);
  if (!buckets.has(k)) buckets.set(k, []);
  buckets.get(k).push(n.text);
}

console.log(`text audit of ${file}`);
console.log(`  rendered text nodes: ${nodes.filter((n) => !classify(n).startsWith('not-rendered')).length}`);
for (const [k, list] of [...buckets].sort()) {
  console.log(`  ${String(list.length).padStart(4)}  ${k}`);
  if (k.startsWith('VIOLATION')) for (const t of list) console.log(`         > ${JSON.stringify(t)}`);
}
const violations = [...buckets].filter(([k]) => k.startsWith('VIOLATION')).reduce((n, [, l]) => n + l.length, 0);
console.log(`\n  VIOLATIONS: ${violations}`);
console.log(`  group labels rendered: ${JSON.stringify([...new Set(buckets.get('group label') || [])])}`);
console.log(`  option values rendered: ${JSON.stringify([...new Set(buckets.get('option value') || [])])}`);
process.exit(violations ? 1 : 0);
