# agentpad13 keycaps

Custom **vertical-wall keycaps** for the agentpad13 — chiclet-style, no taper:
the walls run straight up at 90°, so the caps read as flat-sided tiles rather
than the sculpted, inward-sloping profile of a normal keycap. They fit the
board's 13-key layout (12 × 1U + 1 × 2U) and print stem-down, top-face up, with
no supports.

## One universal cap

There is **one keycap** here. It is MX-compatible and fits **Kailh Box (e.g.
Box Jade), Cherry MX, and Gateron KS-9** alike — those switches all present the
same exposed MX cross (4.00 mm span, 1.30 / 1.10 mm arms, 3.60 mm tall,
confirmed against four manufacturer drawings), so one stem socket and one cap
body serve all of them.

> Earlier versions of this repo shipped a separate, taller "Box" cap on the
> theory that a Kailh Box hides its cross inside a fixed shroud that the cap has
> to swallow. That was wrong: the Box's box is one piece with the *moving* stem,
> so it travels down with the cap and never intrudes. Keycap height has nothing
> to do with switch travel. The cap here is the correct height for all three
> switch families.

You have two independent choices — pick one from each row:

| Choice | Options |
|--------|---------|
| **Top treatment** | **plateau** — a raised rounded-square pad · **dish** — a recessed concave scoop |
| **Footprint size** | **17.5 mm (primary)** · **18.0 mm (alternate)** |

**Top treatment.** Purely feel/look — same walls, footprint, and stem socket, so
they are interchangeable on the board (mix them if you like). Plateau tops are
**6.6 mm** tall, dish tops **6.0 mm**.

**Footprint size.** The board pitch is fixed at 19.05 mm. The **17.5 mm** set is
the primary: a 1U cap is 17.50 × 17.50 mm and the 2U is 36.55 × 17.50 mm,
leaving an even **1.55 mm gap** on every side of every key. The **18.0 mm** set
is the alternate (1U 18.00 × 18.00, 2U 37.00 × 18.00) — tighter gaps, a larger
cap face. Start with 17.5 mm.

## Files

```
keycaps/
  cap_plateau_1u_17p5.stl        1U, plateau, 17.5 mm  (primary)
  cap_plateau_2u_17p5.stl        2U, plateau, 17.5 mm  — plain stem
  cap_plateau_2u_stab_17p5.stl   2U, plateau, 17.5 mm  — with stabilizer sockets
  cap_dish_1u_17p5.stl           1U, dish,    17.5 mm
  cap_dish_2u_17p5.stl           2U, dish,    17.5 mm  — plain stem
  cap_dish_2u_stab_17p5.stl      2U, dish,    17.5 mm  — with stabilizer sockets
  cap_plateau_1u.stl  · cap_plateau_2u.stl  · cap_plateau_2u_stab.stl   ] 18.0 mm
  cap_dish_1u.stl     · cap_dish_2u.stl     · cap_dish_2u_stab.stl      ] alternate
```

`_17p5` is the 17.5 mm primary size; **no suffix** is the 18.0 mm alternate.

### What to print for one keyboard

One agentpad13 needs **12 × 1U + 1 × 2U** in a single top treatment and size.
For the default build — 17.5 mm, plateau tops — that is:

- `cap_plateau_1u_17p5.stl` × **12**
- one 2U: `cap_plateau_2u_stab_17p5.stl` **if you are fitting stabilizers**
  (the board plate is cut for them), or `cap_plateau_2u_17p5.stl` if not.

Swap `plateau` → `dish` for the recessed top, or drop `_17p5` for the 18.0 mm
size — same 12 + 1 recipe.

### The 2U key — stabilizers

The board plate **is** cut for Cherry plate-mount stabilizers at ±11.938 mm. If
you fit them, print the **`_stab`** 2U (it adds the two matching stabilizer
sockets); the plain 2U will not seat once stabilizers are in the plate. If you
run the 2U un-stabilized, print the plain `cap_..._2u_*` instead. Test-fit one
against your actual stabilizers before committing to a batch — the ±11.938 mm
socket spacing is the Cherry spec but hand-fit clearances vary by brand.

## How it mounts

The central stem socket is a cross-slot **4.20 mm across and 3.80 mm deep**. It
grips on the wide axis and floats the narrow one (Cherry's own arrangement):

- **Wide (X) axis — a compliant crush-rib fit.** The bore itself measures
  **1.42 mm**, which is a *hard stop* wider than any MX cross in evidence, so
  the bore can never squeeze the stem. Retention comes instead from **eight
  small integral ribs**, 0.07 mm proud and 0.50 mm wide at the base, that give
  an **effective opening of 1.28 mm**. The ribs deform slightly as the stem
  goes in, so the grip is set by how far a rib yields rather than by how big
  your particular switch's cross turned out to be. A 45° mouth flare and an
  11.3° lead-in ramp mean the stem meets a ramp, never a step.
- **Narrow (Y) axis — a plain 1.25 mm clearance slot**, 0.075 mm/side over the
  1.10 mm arm. It has never been the gripping axis and stays free.

Why compliant rather than a plain dimensional slot: manufacturer drawings put
the MX wide arm at 1.30 ± 0.02 mm, but caliper reports on real switches run
nearer 1.39 mm — a 0.09 mm disagreement, 3.5× the drawing's own tolerance. A
fixed slot has to bet on one of those being right; a rib that yields covers the
whole range. It also absorbs print variance, which lands on the rib crest
instead of going straight into interference.

Four diagonal (45°) webs stiffen the boss against pull-off.

On a **Kailh Box** switch specifically, the boss drops into the square box bore
as a light slip-fit (guiding the cap and resisting wobble), while the four webs
are sized to **clear** that bore — so the same cap that fits a bare
Cherry/Gateron also fits inside a Box's box without fouling. The boss profile
is **lobed** rather than round (a Ø6.00 mm circle intersected with a 5.50 mm
square): across the flats it is still 5.50 mm, holding the same 0.15 mm slip
fit to the bore, but it reaches further out on the diagonals — where the
switch's cross arms are not — which thickens the thinnest socket wall to a
uniform **0.650 mm** at no cost in clearance anywhere.

## Printing

> **Material is a REQUIREMENT, not a preference: use a tough / ABS-like resin
> (elongation at break roughly ≥ 8%), or a rigid filament such as PETG or
> ABS/ASA. Do not use a brittle standard resin.** The socket's retention ribs
> work by *yielding* — in a brittle resin a 0.07 mm rib shatters instead of
> deforming, which throws away the retention and leaves debris inside the
> socket. The same brittleness is what would turn the socket's 0.650 mm wall
> into a crack. If you are ordering these from a print bureau, say so on the
> order, and ask them to stop and check with you rather than substitute a
> standard resin.

Print **stem-down, top-face up, no supports**: the cross slot is then a clean
vertical hole, the ribs are grounded vertical material, and the flat top /
plateau / dish are the upward-facing last layers.

The socket wall is **0.650 mm** at its thinnest, which is below the usual
1.2 mm rule of thumb and is deliberate: that wall sits in the 0.90 mm moat
between the switch's cross and its surrounding box wall, and 0.650 mm is the
geometric ceiling — a 1.0 mm wall would put the boss 0.20 mm *into* the switch
body and the cap would never seat. A print bureau may flag it; the answer is
the material above, not a thicker wall.

**The STL is the final part.** Every dimension is the true finished size of the
keycap — there is **no** process compensation baked in (no FDM undersize
allowance, no SLA light-bleed allowance, no shrink factor). If your printer or
material needs an offset, apply your own slicer / machine compensation
downstream; do not expect the files to pre-correct for your process.

## Licensing

Hardware (this folder included) is licensed **CERN-OHL-W-2.0**, consistent with
the rest of the repository. See the repository root for full terms.
