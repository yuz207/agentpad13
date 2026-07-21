# agentpad13 keycaps

Custom **vertical-wall keycaps** for the agentpad13 — chiclet-style, no taper:
the walls run straight up at 90°, so the caps read as flat-sided tiles rather
than the sculpted, inward-sloping profile of a normal keycap. They are designed
for this board's 13-key layout (12 × 1U + 1 × 2U) and print stem-down, top-face
up, with no supports.

There are three independent choices. Pick one from each row.

| Choice | Options |
|--------|---------|
| **Top treatment** | **plateau** — a raised rounded-square pad · **dish** — a recessed concave top |
| **Footprint size** | **17.5 mm (primary)** · **18.0 mm (alternate)** |
| **Switch target** | **Box (default)** — Kailh Box switches (e.g. Box Jade) · **generic MX** — any standard Cherry-MX-cross switch |

## The three choices, explained

**Top treatment — plateau or dish.** Purely feel/look. The plateau is a raised
pad; the dish is a shallow concave scoop. Both share the same walls, footprint,
and stem socket — they are interchangeable on the board, so mix them if you
like. Print whichever you prefer.

**Footprint size — 17.5 mm or 18.0 mm.** The board's key pitch is fixed at
19.05 mm. The **17.5 mm** set is the primary: a 1U cap is 17.50 × 17.50 mm and
the 2U is 36.55 × 17.50 mm, which leaves an even **1.55 mm gap** on every side
of every key. The **18.0 mm** set is the alternate (1U 18.00 × 18.00 mm, 2U
37.00 × 18.00 mm) — slightly tighter gaps, kept for anyone who prefers a
larger cap face. Start with 17.5 mm.

**Switch target — Box or generic MX.** Both mount on the MX-compatible cross,
but the two switch families present that cross differently, so the caps are
**not** the same height:

- On a **Kailh Box** switch the cross sits flush with the top of the box
  housing, so the cap needs a deeper socket — and therefore a taller body — to
  reach down over the housing and grip the cross. Box caps: **plateau 9.9 mm,
  dish 9.3 mm** tall.
- On a **standard Cherry-MX** switch the cross protrudes above the housing, so
  a shorter cap reaches it. MX caps are correspondingly lower: **plateau
  6.6 mm, dish 6.0 mm** tall.

Use the **Box** files (the default) if you are running Kailh Box switches; use
the **generic MX** files for ordinary Cherry-MX-style switches. Everything else
about the caps is identical between the two.

## Files

```
keycaps/
  box/       Box-switch caps (default) — 17.5 mm + 18.0 mm, plateau + dish
  mx/        generic Cherry-MX caps    — 17.5 mm + 18.0 mm, plateau + dish
  plates/    print-ready batch sheets (Box) — enough caps for 5 keyboards
```

`_17p5` in a filename is the 17.5 mm primary size; **no suffix** is the 18.0 mm
alternate. `_stab` is explained under 2U below.

### What to print for one keyboard

One agentpad13 needs **12 × 1U + 1 × 2U** in a single top treatment and size.
For the default build — Box switches, 17.5 mm, plateau tops — that is:

- `box/cap_plateau_1u_17p5.stl` × **12**
- `box/cap_plateau_2u_17p5.stl` × **1**

Swap `plateau`→`dish` for the recessed top, drop `_17p5` for the 18.0 mm size,
or use the `mx/cap_mx_*` files for Cherry-MX switches — same 12 + 1 recipe.

### The 2U key (`_stab` variants)

The board ships **without** stabilizers, so the default 2U cap
(`cap_..._2u_*`) has a plain stem and is the one to print. The `_stab` files
(`cap_..._2u_stab_*`) add Cherry plate-mount **stabilizer sockets** for builders
who fit stabilizers to the 2U position — print one and test-fit it against your
stabilizer before committing to a batch.

### Batch plates (`plates/`) — optional, for printing 5 units at once

Print-ready sheets that tile many caps per plate, for anyone making a run of
keyboards. They are the **Box** caps at both sizes:

- `plate_<treatment>_1u_<size>_x20_{1of3,2of3,3of3}.stl` — 20 × 1U per sheet,
  three sheets = **60 × 1U** (= 12 × 1U for 5 keyboards).
- `plate_<treatment>_2u_<size>_x5.stl` — **5 × 2U** on one sheet (= 1 × 2U for
  5 keyboards).

So one full 5-keyboard set of one style is the three `_1u_..._x20` sheets plus
the one `_2u_..._x5` sheet. For single builds, print the individual caps from
`box/` instead. (Generic-MX caps are supplied as individual files only.)

## Printing

**Any common rigid keycap material works — the caps are not restricted to one.**
The stem socket is engineered for this: four diagonal (45°) webs stiffen the
boss around a **1.25 mm square cross-slot**, sized to press-fit safely across
the full manufacturing tolerance band of the MX cross, and it was validated in
**both SLA resin and FDM**. PETG, ABS/ASA, or resin all work. Print stem-down,
top-face up, no supports.

**The STL is the final part.** Every dimension in these files is the true,
finished physical size of the keycap — there is **no** process compensation
baked in (no FDM undersize allowance, no SLA light-bleed allowance, no shrink
factor). If your printer or material needs an offset, apply your own slicer /
machine compensation downstream. Do not expect the files to pre-correct for
your process.

## Licensing

Hardware (this folder included) is licensed **CERN-OHL-W-2.0**, consistent with
the rest of the repository. See the repository root for full terms.
