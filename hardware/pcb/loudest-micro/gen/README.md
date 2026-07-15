# Schematic generator (source of `loudest-micro.kicad_sch`)

The `.kicad_sch` is a **build artifact**. It is generated from these scripts so the netlist is
diffable, reviewable, and regenerable. DRAFT — pending human review (see `../../SCHEMATIC-REVIEW.md`).

| File | Role |
|---|---|
| `sexp.py` | Minimal, robust S-expression serializer (nested Python lists → KiCad text) |
| `kschem.py` | Flat-schematic emitter: symbol defs, placement, per-pin stub + global-label / power-symbol, no-connects, power flags |
| `build_loudest.py` | **The design.** Every component, value, MPN/LCSC/JLC-tier, footprint note, and pin→net map |
| `bom_gen.py` | Parses the generated `.kicad_sch` and emits `../../BOM-draft.csv` (order-grouped) |

## Regenerate

```bash
python3 build_loudest.py ..            # writes ../loudest-micro.kicad_sch + .kicad_pro
python3 bom_gen.py ../loudest-micro.kicad_sch ../../BOM-draft.csv
```

## Connectivity model

Single flat sheet; connectivity is by **net name** (same-named `global_label` / `power:*` symbols
form one net), so the netlist is independent of routing geometry. Every symbol is placed at rotation 0
so each pin's absolute position is `(x+px, y−py)`; the stub wire + label are emitted from the same pin
table, guaranteeing the label lands exactly on the pin. This is the reason the netlist is provably
correct without a router.

## Validation

No `kicad-cli`/KiCad in the authoring environment. Validated with the **kicad-happy** schematic
analyzer (`analyze_schematic.py`, KiCad 5–10 s-expression parser + ERC-equivalent detectors):
**0 errors**, and every load-bearing net asserted against intent. A human should open the result in
KiCad 9 to run native ERC and bind footprints.

> `bom_gen.py` imports `sexp_parser` from the local kicad-happy skill install path; adjust the
> `sys.path.insert(...)` line if that path differs on another machine.
