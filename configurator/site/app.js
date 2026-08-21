/**
 * app.js — boot. Loads the generated catalog if the build has produced one,
 * otherwise falls back to the checked-in STUB data (with a console warning),
 * then wires: state -> rules -> {rail, sheet, viewer}.
 *
 * Data sources, in order:
 *   ../build/out/   generated from release/MANIFEST.md by the build script
 *   data-stub/      hand-authored stand-ins, every file marked "STUB": true
 *
 * Release deep links are repo-root-relative, so the site must be served with
 * the repository root reachable at RELEASE_BASE.
 */

import { createStore, initialState } from './state.js';
import { derive } from './rules.js';
import { buildSheet } from './sheet.js';
import { buildRail, renderSheet, wireSheet } from './ui.js';
import { createViewer } from './viewer.js';

const RELEASE_BASE = '../../';
const GENERATED = '../build/out/';
const STUB = 'data-stub/';

const getJSON = async (url) => {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
};

async function loadFrom(base) {
  const [catalog, positions, costs] = await Promise.all(
    ['catalog.json', 'positions.json', 'costs.json'].map((n) => getJSON(base + n)),
  );
  return { base, catalog, positions, costs };
}

async function loadData() {
  let bundle;
  try {
    bundle = await loadFrom(GENERATED);
  } catch (err) {
    console.warn(`[agentpad13] no generated catalog (${err.message}) — using the STUB data in ${STUB}`);
    bundle = await loadFrom(STUB);
  }
  if (bundle.catalog.STUB) console.warn('[agentpad13] catalog is a STUB: meshes are primitive stand-ins and file links are the real release paths.');
  const [finishes, rules] = await Promise.all([getJSON('finishes.json'), getJSON('rules.json')]);
  return { ...bundle, finishes, rules };
}

function allMeshes(catalog) {
  const out = [];
  const walk = (o) => {
    if (Array.isArray(o)) return o.forEach(walk);
    if (o && typeof o === 'object') {
      for (const [k, v] of Object.entries(o)) {
        if (k === 'mesh' && typeof v === 'string') out.push(v); else walk(v);
      }
    }
  };
  walk(catalog);
  return out;
}

async function boot() {
  const data = await loadData();
  const store = createStore(initialState(data));

  const viewer = createViewer({ canvas: document.getElementById('view'), data, meshBase: data.base });
  const rail = buildRail(document.getElementById('rail'), data, store);
  const sheetBody = document.getElementById('sheet-body');
  wireSheet(document.getElementById('sheet'), document.getElementById('sheet-handle'));

  function update() {
    const state = store.get();
    const derived = derive(state, data);
    rail.sync(state, derived);
    renderSheet(sheetBody, buildSheet(state, data, derived), RELEASE_BASE);
    viewer.apply(state, derived);
  }
  store.subscribe(update);
  update();

  const dark = matchMedia('(prefers-color-scheme: dark)');
  viewer.setTheme(dark.matches);
  dark.addEventListener('change', (e) => viewer.setTheme(e.matches));

  viewer.preload(allMeshes(data.catalog));
  document.documentElement.dataset.ready = 'true';
}

boot().catch((err) => console.error('[agentpad13] boot failed', err));
