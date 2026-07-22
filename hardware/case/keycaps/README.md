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

The central stem socket is a **1.25 mm square cross-slot** — the MX wide arm
(1.30) minus 0.05 mm of designed interference, so it grips on the wide axis and
floats the narrow one (Cherry's own arrangement). It press-fits safely across
the whole manufacturing tolerance band of the MX cross and was validated in both
SLA resin and FDM. Four diagonal (45°) webs stiffen the boss against pull-off.

On a **Kailh Box** switch specifically, the Ø5.5 mm boss drops into the square
box bore as a light slip-fit (guiding the cap and resisting wobble), while the
four webs are sized to **clear** that box bore — so the same cap that fits a
bare Cherry/Gateron also fits inside a Box's box without fouling.

## Printing

**Any common rigid keycap material works** — PETG, ABS/ASA, or resin. Print
**stem-down, top-face up, no supports**: the cross slot is then a clean vertical
hole and the flat top / plateau / dish are the upward-facing last layers.

**The STL is the final part.** Every dimension is the true finished size of the
keycap — there is **no** process compensation baked in (no FDM undersize
allowance, no SLA light-bleed allowance, no shrink factor). If your printer or
material needs an offset, apply your own slicer / machine compensation
downstream; do not expect the files to pre-correct for your process.

## Licensing

Hardware (this folder included) is licensed **CERN-OHL-W-2.0**, consistent with
the rest of the repository. See the repository root for full terms.
