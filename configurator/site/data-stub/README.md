# data-stub — stand-in data for the configurator site

The site loads `../build/out/{catalog,positions,costs}.json` first. If the build
has not produced them, it falls back to this directory and says so in the
console. Everything here is **marked `"STUB": true`** and exists so the page —
layout, rules, build sheet, viewer placement — can be developed and tested
before the pipeline lands.

Regenerate the meshes with:

```sh
node configurator/site/tools/make_stub_meshes.mjs
```

## What is real and what is not

| | status |
|---|---|
| `release/…` paths in `catalog.json` | **real** — every one resolves in the release bundle, and `configurator/tests/site_data.test.mjs` fails if one does not |
| geometry in `positions.json` | **real** — read off `contract_v4.json` and `agentpad13_case_v2.py` |
| `meshes/*.glb` | **stubs** — boxes, rounded prisms, rings and cylinders at the real footprints and the real z stack. Not the shipping geometry |
| `costs.json` | empty by design: `updated: null`, so the sheet renders no prices |

The stub `board.glb` additionally carries the EC11 body and the joystick body
(envelopes from the case script's keep-outs) so the plate's encoder and stick
openings read as hardware rather than as holes into an empty case. The real
`board.glb` is a bare slab, so with generated data those two openings show the
tray floor.

## Frame and placement — the same contract as the generated data

Meshes are already in glTF's **Y-up right-handed** space. A board-frame
position `(x, y)` at height `z` is placed at `(x, z, y)` — the **determinant
−1** swap `positions.json` documents. That swap is what turns the case model's
*left-handed* design frame into the correctly handed real device; the usual
det +1 Z-up→Y-up rotation `(x, z, −y)` would render the **mirror image**.
`viewer.js` therefore applies no rotation of its own.

- **baked** — `board`, `plate`, `band_*`, `tray`, `base_*` carry their assembly
  position in the vertex data: load and add.
- **instance** — `cap_*`, `knob_*`, `stick_cap_*` sit at their own local
  origin. Caps start at `y = 0` (bottom rim) and are placed at
  `keycap_seat_z`; knobs and stick caps carry their absolute height and are
  placed at `(x, 0, y)`.

`../assets/switch_mx.glb` is **not** catalog data: MX switches are user-supplied
and no release file exists for them, so the site owns that stand-in.

## Deltas between this stub and `build/out/` (2026-08-20)

Both files are kept key-for-key in step, and
`site_data.test.mjs` fails when they drift. Two fields exist here that the
generated data does not carry yet:

1. `catalog.firmware.flash` — the flash command line the spec's fixed footer
   requires (`release/firmware/BRING-UP.md` step 1). `sheet.js` falls back to a
   constant when it is absent.
2. `positions.base.tilt_deg` — per-variant base tilt, so the viewer can level a
   wedge or pedestal on the desk (`agentpad13_base_params.json`
   `variants[].tilt_deg`). `viewer.js` falls back to a constant when absent.

`board.texture` is `null` here (a stub has no board render to show); the viewer
uses the mesh's own authored material and texture when the generated data
supplies one.
