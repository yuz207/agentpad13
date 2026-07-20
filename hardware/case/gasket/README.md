# Optional PORON ledge-gasket kit — agentpad13 v2

A small, **optional** foam accessory for the v2 band. It adds a gentle downward
preload on the PCB rim by seating user-cut adhesive PORON segments under the
band's rabbet ledge.

> **This is OPTIONAL.** The bare band ledge already sits `+0.3 mm` above the PCB
> top rim and is the sandwich backstop on its own. The gasket only converts that
> `0.3 mm` air gap into a soft, always-in-contact preload. Skip it and nothing
> is wrong.

> **No design geometry changed anywhere.** This kit is a paper/foam accessory
> *derived* from the existing band geometry. The band, tray, plate and board
> files (and their md5s) are byte-for-byte untouched — the band STL remains
> `36980cc2ff011dc32d923fb04f7429f7`. Nothing here is ordered from a fab.

---

## What the ledge is (derived, not invented)

The band's inner wall steps inward over a `+0.3 .. +3.4 mm` z-band to form a
**rabbet ledge** — a `1.2 mm`-wide perimeter ring the FR4 plate drops onto. That
ring is cut in the case model's `band()` step from these constants
(read from the model, never retyped):

| quantity | value | source |
|---|---|---|
| ledge width `LEDGE_W` | `1.2 mm` | case model |
| ledge underside `LEDGE_Z0` | `+0.3 mm` above PCB top | case model |
| band inner wall `INNER_W × INNER_H` (ledge OUTER outline) | `84.8 × 100.6 mm`, R`5.6` | derived `PCB + 2·PCB_CLEARANCE`, `OUTER_R − WALL` |
| ledge INNER outline `INNER_ − 2·LEDGE_W` | `82.4 × 98.2 mm`, R`4.4` | derived |
| PCB outline | `84.2 × 100.0 mm` octagon | the board (`hardware/pcb/agentpad13/agentpad13.kicad_pcb`) |

So the ledge underside is a flat `1.2 mm` ring at `z = +0.3`. The PCB edge sits
`PCB_CLEARANCE = 0.3 mm` inside the band wall, so of that `1.2 mm` strip the
inner **`0.9 mm` overhangs the PCB rim** (the preload contact patch) and the
outer `0.3 mm` hangs over the edge-clearance gap. *(Verified against the actual
band STL: a plane-slice at y=50 / x=25 / x=60 shows the underside is a flat
`z = 0.300` face on all four sides — the code's inner-edge print chamfer was
OCCT-refused and left square, so there is a full flat `1.2 mm` face to bond to.)*

## The compression math

- PORON segment nominal thickness: **`0.5 mm`**
- Gap it compresses into (ledge underside → PCB top): **`0.3 mm`**
- Strain = `(0.5 − 0.3) / 0.5` = **`40 %`**

PORON's useful compression band is ~`20–50 %`, so `40 %` sits in the sweet spot:
a gentle, spring-back preload — not a hard clamp. Contact/preload develops over
the `0.9 mm`-wide strip that overhangs the board rim.

## Material

- **0.5 mm PORON** microcellular urethane foam sheet (any PORON 4701-30 /
  92-class soft grade; generic soft PORON is fine — this is a compliance pad,
  not a seal).
- **Adhesive-backed**: a **3M 468MP / 9471LE-class** (or equivalent) high-tack
  transfer-adhesive backing. Any thin PSA foam tape of `0.5 mm` total thickness
  works.
- **Quantity**: a single `100 × 100 mm` sheet is *many times* more than needed —
  all 10 segments together are only ~`180 mm²` (a `100 × 100` sheet is
  `10 000 mm²`, i.e. **>50× surplus**; buy the smallest sheet sold).

## The segments (10 total)

`~15 mm` long × `1.2 mm` wide (matches the ledge width), placed along the four
sides and **clear of the four corner caps and the USB aperture**:

| side | count | positions (board coords, mm) | strip |
|---|---|---|---|
| West  | 3 | y = 25, 50, 75 | x −0.3 … 0.9 |
| East  | 3 | y = 25, 50, 75 | x 83.3 … 84.5 |
| North | 2 | x = 24.9, 59.3 (either side of the USB) | y −0.3 … 0.9 |
| South | 2 | x = 24.9, 59.3 | y 99.1 … 100.3 |

Corner keep-out = `BOSS_CENTERS ± SOCKET_D` (10 mm around each corner-cap
socket); USB keep-out = the `10 mm` J1 aperture span at x `42.1 ± 5`, plus a
`1 mm` margin. The template draws both keep-outs so you can see why the segments
stop where they do. Segments are all identical — orientation does not matter.

## Cut and place

1. **Print `gasket_template.pdf` at 100% / actual size** (turn OFF "fit to
   page" / "shrink to fit"). Measure the 50 mm scale bar — it must read 50 mm.
2. Lay the PORON sheet over the template (or cut free-hand to the listed size).
   With a sharp **X-Acto / craft knife and a steel straightedge**, cut 10
   rectangles `15 × 1.2 mm`. The width may be trimmed slightly (`1.0–1.2 mm`) —
   err narrow rather than wide so no foam overhangs the ledge inner edge.
   *(Craft-cutter users: `gasket_segments.dxf` has the 10 rectangles in mm.)*
3. **Peel and stick each segment to the BAND ledge underside — NOT to the
   board.** Reach up into the band from the open (tray) side; the ledge is the
   `1.2 mm` shelf `0.3 mm` down from the plate recess. Press the foam flat, its
   outboard edge against the band inner wall, following the side positions
   above. Skip the four corners and the USB mouth.
4. Assemble as normal. The plate/screws set the stack height; the foam simply
   takes up the `0.3 mm` and lightly loads the board rim.

If a segment peels or you want more/less preload, add or remove segments — the
kit is fully reversible and does not affect any fit.

## Files

| file | what |
|---|---|
| `gasket_template.svg` | 1:1 source (mm units); ledge ring + cut rects + scale bar |
| `gasket_template.pdf` | print-ready, exactly 1:1 (page 190 × 250 mm; fits A4 & US-Letter) |
| `gasket_template.png` | raster preview |
| `gasket_segments.dxf` | the 10 cut rectangles only, mm units (craft cutters) |

**1:1 provenance.** The SVG declares `width="190mm" height="250mm"` with
`viewBox="0 0 190 250"`, so 1 user unit = 1 mm by construction and the scale bar
is authored at exactly 50 units. The PDF was produced with Inkscape and its page
box was re-measured with PyMuPDF at **190.000 × 250.000 mm** — a 1:1 page, so
any element (the 50 mm bar, the 15 mm segments) prints at true size.
