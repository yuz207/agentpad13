/**
 * site_lighting.test.mjs — the LED rig: what is lit, and how hard.
 *
 * viewer.js needs WebGL and cannot run here, so the two decisions worth
 * testing were pulled out into site/lighting.js — pure numbers and pure
 * predicates. This suite asserts the OWNER RULES on them:
 *
 *   round 4, verbatim: "Why is there any glow showing through band even when
 *   opaque?"  ->  an opaque band emits NO band glow at all.
 *
 *   round 4, verbatim: "lit means the board LEDs under the keys too!"  ->  the
 *   per-key half is on every board, gated on nothing but the light switch.
 *
 *   round 4, verbatim: "It's just a hard band which is ridiculous. Should
 *   really look like a diffuse glow."  ->  and the retune that followed it,
 *   "That is a diffuse glow — but hugely overcooked", which is why the budget
 *   below is asserted as a LADDER with the bloom threshold between its rungs.
 */

import { suite, ok, eq, loadData } from './site_harness.mjs';
import { initialState, withPath } from '../site/state.js';
import { GAIN, BLOOM, BAND_LAMP, WHITE_MIX, LUM, emissiveRGB, bandGlow, keyGlow } from '../site/lighting.js';

const S = suite('site_lighting');
const data = loadData();
const base = () => initialState(data);
const lit = (s) => withPath(s, 'lighting.on', true);

/* The palette, in linear light — the space the emitters are mixed in. */
const linear = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  const srgb = (v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return { r: srgb(((n >> 16) & 255) / 255), g: srgb(((n >> 8) & 255) / 255), b: srgb((n & 255) / 255) };
};

S.test('an OPAQUE band emits NO band glow at all — owner ruling, round 4', () => {
  /* Verbatim, from the question that made this a rule: "Why is there any glow
     showing through band even when opaque?" The answer was that the ribbon
     stayed lit and its seam spill, its skirt and its lamps painted the deck
     and the outside of the wall, so a solid band still had a glowing edge.
     Nothing about the band may survive the checkbox coming off. */
  const s = lit(base());
  eq(s.band.translucent, true, 'the default band IS translucent (see finishes.json defaults)');
  eq(bandGlow(s), true, 'the default lit build glows at the band');
  eq(bandGlow(withPath(s, 'band.translucent', false)), false,
    'an opaque band must build no ribbon, no seam, no skirt, no lamp and no desk pool');
});

S.test('the band half needs all THREE: lit, the band you ordered, and light through it', () => {
  for (const on of [false, true]) {
    for (const led of ['no', 'yes']) {
      for (const clear of [false, true]) {
        let s = withPath(withPath(base(), 'lighting.on', on), 'led', led);
        s = withPath(s, 'band.translucent', clear);
        eq(bandGlow(s), on && led === 'yes' && clear,
          `lit=${on} led=${led} translucent=${clear}`);
      }
    }
  }
});

S.test('the per-key LEDs are on EVERY board: only the light switch gates them', () => {
  /* Round 4: "lit means the board LEDs under the keys too!" Thirteen LEDs sit
     under the switches whatever you ordered, so a board with no LED band and
     an opaque case still lights all thirteen — which is exactly what the
     Lighting section being offered unconditionally promises. */
  let s = lit(withPath(base(), 'led', 'no'));
  s = withPath(s, 'band.translucent', false);
  s = withPath(s, 'tray.translucent', false);
  eq(keyGlow(s), true, 'no band, opaque case: the under-key LEDs are still lit');
  eq(bandGlow(s), false, '...and the band half is dark, which is the whole point');
  eq(keyGlow(base()), false, 'unlit is unlit');
  eq(keyGlow(withPath(lit(s), 'view.switches', false)), true,
    'hiding the switches moves the emitter into the plate hole; it never puts it out');
});

S.test('the ladder is quoted in LUMINANCE, so every colour blooms alike', () => {
  /* A saturated hue carries very little luminance — pure blue is ~7% of white —
     and UnrealBloomPass thresholds on luminance. Scaling every hue by the same
     multiplier therefore made blue LEDs silently stop blooming. Normalising to
     luminance is what lets ONE threshold serve the whole palette. */
  for (const f of data.finishes.finishes) {
    for (const gain of [GAIN.HOT, GAIN.WARM, GAIN.DIM]) {
      const e = emissiveRGB(linear(f.hex), gain);
      const l = LUM(e);
      ok(Math.abs(l - gain) < 1e-3, `${f.id} at gain ${gain} reached luminance ${l.toFixed(3)}`);
      ok(e.r >= 0 && e.g >= 0 && e.b >= 0, `${f.id}: negative channel`);
    }
  }
  ok(WHITE_MIX > 0.2 && WHITE_MIX < 0.6, 'a hot LED is white in the middle and keeps its hue in the falloff');
  const blue = emissiveRGB(linear('#1B57C6'), GAIN.HOT);
  ok(blue.b > blue.r && blue.b > blue.g, 'and the hue must survive the white mix');
});

S.test('the bloom threshold sits BETWEEN the rungs: HOT flares, nothing else does', () => {
  ok(GAIN.HOT > BLOOM.threshold, `the source must clear the threshold: ${GAIN.HOT} vs ${BLOOM.threshold}`);
  for (const [name, g] of [['WARM', GAIN.WARM], ['DIM', GAIN.DIM], ['FAINT', GAIN.FAINT]]) {
    ok(g < BLOOM.threshold, `${name} (${g}) must never bloom: it is the falloff, not the source`);
  }
  ok(GAIN.WARM > GAIN.DIM && GAIN.DIM > GAIN.FAINT, 'the shoulder has to descend');
  /* And the threshold has to stay ABOVE the ~1.6 linear a white matte face
     reaches under this key light, or the DEVICE blooms and there is no subject
     left in the picture. */
  ok(BLOOM.threshold > 1.7, `a lit white face would bloom at threshold ${BLOOM.threshold}`);
});

S.test('the retune came DOWN: this is a glow budget, not a flare budget', () => {
  /* The dying words of the cut before this one: "That is a diffuse glow — but
     hugely overcooked. Retuning the whole energy budget down." That cut ran
     HOT 7.0, bloom strength 0.6 over threshold 2.4 and six 260 cd lamps, and
     it washed the band out to flat white with no colour left in it. */
  ok(GAIN.HOT <= 4.0, `HOT ${GAIN.HOT}: over 4 and the band clips to white again`);
  ok(BLOOM.strength <= 0.6, `bloom strength ${BLOOM.strength}: the device stays legible THROUGH the glow`);
  ok(BLOOM.radius >= 0.6, 'a wide, soft radius is what makes it read as light rather than as a halo');
  ok(BAND_LAMP.intensity <= 120, `${BAND_LAMP.intensity} cd inside the case blows the tray out`);
  eq(BAND_LAMP.decay, 2, 'inverse-square, like light');
});

S.run();
