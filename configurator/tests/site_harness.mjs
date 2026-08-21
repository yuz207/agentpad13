/**
 * site_harness.mjs — 60-line assert harness for the configurator site tests.
 * No dependencies, no framework. Each test file builds a suite and runs it at
 * import time; site_run.mjs imports them all and reports the total.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const TALLY = { pass: 0, fail: 0, failures: [] };

const HERE = dirname(fileURLToPath(import.meta.url));
export const REPO = join(HERE, '..', '..');
export const SITE = join(REPO, 'configurator', 'site');

export function suite(name) {
  const cases = [];
  return {
    test: (label, fn) => cases.push({ label, fn }),
    run() {
      console.log(`\n${name}`);
      for (const c of cases) {
        try {
          c.fn();
          TALLY.pass++;
          console.log(`  PASS  ${c.label}`);
        } catch (err) {
          TALLY.fail++;
          TALLY.failures.push(`${name} :: ${c.label}: ${err.message}`);
          console.log(`  FAIL  ${c.label}\n        ${err.message}`);
        }
      }
    },
  };
}

export function ok(cond, msg) {
  if (!cond) throw new Error(msg || 'expected truthy');
}

export function eq(actual, expected, msg) {
  if (!Object.is(actual, expected)) {
    throw new Error(`${msg || 'not equal'}\n        actual:   ${JSON.stringify(actual)}\n        expected: ${JSON.stringify(expected)}`);
  }
}

export function deep(actual, expected, msg) {
  const a = JSON.stringify(actual), b = JSON.stringify(expected);
  if (a !== b) throw new Error(`${msg || 'not deep-equal'}\n        actual:   ${a}\n        expected: ${b}`);
}

export function throws(fn, msg) {
  let threw = false;
  try { fn(); } catch { threw = true; }
  if (!threw) throw new Error(msg || 'expected a throw');
}

/** Load the stub data bundle the site ships with. */
export function loadData() {
  const j = (p) => JSON.parse(readFileSync(p, 'utf8'));
  return {
    catalog: j(join(SITE, 'data-stub', 'catalog.json')),
    positions: j(join(SITE, 'data-stub', 'positions.json')),
    costs: j(join(SITE, 'data-stub', 'costs.json')),
    finishes: j(join(SITE, 'finishes.json')),
    rules: j(join(SITE, 'rules.json')),
  };
}

/** Deep-freeze, so a purity violation throws instead of passing quietly. */
export function freeze(o) {
  Object.freeze(o);
  for (const v of Object.values(o)) if (v && typeof v === 'object') freeze(v);
  return o;
}
