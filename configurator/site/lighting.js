/**
 * lighting.js — the LED rig's ENERGY BUDGET and the two gates that decide what
 * is lit at all. PURE: no THREE, no DOM, so `configurator/tests/site_lighting.
 * test.mjs` asserts the budget and the owner's rules under node, without a
 * WebGL context. viewer.js turns these numbers into geometry.
 *
 * WHY A BUDGET AND NOT LITERALS. The first cut of the glow was tuned by eye,
 * one constant at a time, and it ended up "a diffuse glow — but hugely
 * overcooked": a blown-white ribbon with no hue left in it and a device you
 * could no longer read. The fix is not a smaller number here and there, it is
 * ONE ladder that every emitter stands on, with the bloom threshold set BETWEEN
 * two of its rungs. Then "does this bloom?" is answered by the ladder rather
 * than by a hue's accident of luminance.
 *
 * THE LADDER IS IN LUMINANCE, and that is the whole trick — see emissiveRGB.
 *
 *   HOT    3.0   above the bloom threshold: a light SOURCE, and the only thing
 *                in the render allowed to flare
 *   WARM   1.2   below it: bright, clipping toward white, but never blooming —
 *                this is the shoulder that gives the source a soft edge
 *   DIM    0.35  a tinted surface, not a light
 *   FAINT  0.03  the last rung before nothing, so the source fades out instead
 *                of ending on a line
 *
 * The bloom THRESHOLD sits at 1.9: above the ~1.6 a white matte face reaches
 * under this key light (so the device itself stays crisp) and comfortably below
 * HOT (so every LED flares, whatever colour it is).
 */

/** Rec. 709 relative luminance — the same weights UnrealBloomPass thresholds on
 *  (vendor/three/addons/shaders/LuminosityHighPassShader.js). */
export const LUM = (c) => 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;

/**
 * How far a hot emitter is mixed toward white before it is scaled. A bright LED
 * IS white in the middle — the hue survives in the falloff — and the mix also
 * keeps the scale factor sane: a fully saturated blue normalised straight to
 * luminance 3 would need a blue channel near 40.
 */
export const WHITE_MIX = 0.35;

/**
 * The emitter colour for a base hue at a rung of the ladder, as plain linear
 * {r, g, b} well above 1.0 (HDR — the render carries it in a HalfFloat buffer
 * and the bloom pass is what turns it into light).
 *
 * NORMALISED TO LUMINANCE, deliberately: a saturated hue carries very little of
 * it — pure blue is ~7% of white — so scaling every hue by the same multiplier
 * makes a blue LED roughly fourteen times dimmer than a white one, and it
 * silently drops under the bloom threshold. Dividing by the mixed colour's own
 * luminance makes `gain` mean the same brightness for every colour in the
 * palette, which is what lets ONE threshold work for all of them.
 */
export function emissiveRGB(base, gain, whiteMix = WHITE_MIX) {
  const w = whiteMix * Math.min(1, Math.max(0, (gain - 1) / 2));
  const c = {
    r: base.r + (1 - base.r) * w,
    g: base.g + (1 - base.g) * w,
    b: base.b + (1 - base.b) * w,
  };
  const s = gain <= 0 ? 0 : gain / Math.max(LUM(c), 1e-4);
  return { r: c.r * s, g: c.g * s, b: c.b * s };
}

/** The ladder, and the gains every piece of the rig is quoted in. */
export const GAIN = { HOT: 3.0, WARM: 1.2, DIM: 0.35, FAINT: 0.03 };

/**
 * Bloom. `strength` is modest on purpose: the device has to stay legible
 * THROUGH the glow. The first cut ran 1.05/0.6 over a HOT of 12 and produced a
 * nuclear flare; the second ran 0.6 over a HOT of 7 and still washed the band
 * out to flat white. This is the third, and the rule it follows is that the
 * BAND'S OWN COLOUR must survive in the render.
 */
export const BLOOM = { strength: 0.5, radius: 0.75, threshold: 1.9 };

/**
 * Point-light intensity for the six unshadowed lamps inside a lit band, in
 * three.js candela (decay 2, so illuminance is intensity / r²). At 260 they
 * blew the tray and the module bodies out; this is the level where the band
 * reads as internally lit and the parts around it merely respond.
 */
export const BAND_LAMP = { intensity: 85, distance: 170, decay: 2 };

/**
 * THE BAND HALF. Owner rule, round 4, from the question "Why is there any glow
 * showing through band even when opaque?" — an OPAQUE BAND EMITS NO BAND GLOW
 * AT ALL. Not a dimmer ribbon, not a seam hairline, not a lamp inside: nothing.
 *
 * Three things have to be true before any band emitter exists:
 *   lighting.on         you asked for the render to be lit
 *   led === 'yes'       the board you are ordering HAS the ten side-firing LEDs
 *   band.translucent    and the wall in front of them can pass light
 *
 * The third is the new one. It is also the physical one: the ribbon, the seam
 * annulus at the deck, the skirt down the outside and the pool on the desk are
 * all light that came THROUGH the band, so an opaque wall leaves the band edge
 * dark and the under-key LEDs are the whole of `lit`.
 */
export function bandGlow(state) {
  return (state.lighting || {}).on === true
    && state.led === 'yes'
    && (state.band || {}).translucent === true;
}

/**
 * THE PER-KEY HALF — thirteen LEDs under the switches. Round 4: "lit means the
 * board LEDs under the keys too!" They are on EVERY board, so this half is
 * gated on nothing but the light switch: not on the LED band you ordered, not
 * on the band's translucency, not on the case at all.
 */
export function keyGlow(state) {
  return (state.lighting || {}).on === true;
}
