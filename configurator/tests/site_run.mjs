/**
 * site_run.mjs — runs every configurator-site test suite.
 *
 *   node configurator/tests/site_run.mjs
 *
 * Each suite also runs standalone (`node configurator/tests/site_rules.test.mjs`).
 */

import { TALLY } from './site_harness.mjs';

await import('./site_rules.test.mjs');
await import('./site_sheet.test.mjs');
await import('./site_data.test.mjs');
await import('./site_lighting.test.mjs');
await import('./site_selfcontained.test.mjs');

console.log(`\n${TALLY.pass} passed, ${TALLY.fail} failed`);
if (TALLY.fail) {
  console.log('\nfailures:');
  for (const f of TALLY.failures) console.log(`  - ${f}`);
  process.exit(1);
}
