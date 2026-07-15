#!/usr/bin/env python3
"""Extract a grouped BOM from the generated loudest-micro.kicad_sch."""
import sys, csv, re
sys.path.insert(0, "~/.claude/plugins/cache/kicad-happy/kicad-happy/2.0.0/skills/kicad/scripts")
from sexp_parser import parse_file, find_all, get_property, get_value

SCH = sys.argv[1]
OUT = sys.argv[2]
root = parse_file(SCH)

comps = []
for sym in find_all(root, "symbol"):
    if len(sym) > 1 and isinstance(sym[1], str):
        continue  # lib_symbols entry
    lib = get_value(sym, "lib_id") or ""
    if lib.startswith("power:"):
        continue
    ref = get_property(sym, "Reference") or ""
    if ref.startswith("#"):
        continue
    props = {p[1]: p[2] for p in sym if isinstance(p, list) and p[0] == "property" and len(p) >= 3}
    dnp = get_value(sym, "dnp") == "yes"
    fp = props.get("Footprint", "")
    comps.append(dict(
        ref=ref, value=props.get("Value", ""), descr=props.get("Description", ""),
        fp=fp, mpn=props.get("MPN", ""), lcsc=props.get("LCSC", ""),
        jlc=props.get("JLC", ""), dnp="DNP" if dnp else "",
    ))

# clean family descriptions (order-BOM view; positions live in References)
DESC = {
    "100n": "100nF X7R bypass / decoupling / RC, 0402",
    "1u": "1uF X5R, 0402 (RP2040 VREG + LDO in/out)",
    "10u": "10uF X5R, 0805 (rail bulk)",
    "15p": "15pF C0G crystal load, 0402",
    "5.1k": "5.1k 1% USB-C CC pulldown, 0402",
    "27": "27R USB D+/D- series, 0402",
    "1k": "1k series (XOUT / BOOTSEL / joystick RC), 0402",
    "10k": "10k RUN pull-up, 0402",
    "4.7k": "4.7k I2C SDA/SCL pull-up, 0402",
    "0R": "0R AHLB strap (GND=active-high), 0402",
    "MX_Hotswap": "MX hotswap key switch, direct-pin GP0-12 (dual-socket combined FP)",
    "SK6812MINI-E": "RGB LED reverse-mount, per-key + layer indicator",
    "SK6812-SIDE": "RGB LED side-firing 4020, underglow",
}
# group by orderable part signature (NOT per-instance description)
groups = {}
for c in comps:
    key = (c["value"], c["fp"], c["mpn"], c["lcsc"], c["jlc"], c["dnp"])
    groups.setdefault(key, {"refs": [], "descr": c["descr"]})["refs"].append(c["ref"])

def refsort(r):
    m = re.match(r"([A-Za-z_]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)

rows = []
for key, g in groups.items():
    value, fp, mpn, lcsc, jlc, dnp = key
    refs = g["refs"]
    descr = DESC.get(value, g["descr"])
    refs_sorted = sorted(refs, key=refsort)
    # verification flags
    flags = []
    if "TBD" in fp or "TBD" in lcsc or "TBD" in mpn:
        flags.append("footprint/part TBD at layout")
    if lcsc in ("", "C_TBD_verify"):
        flags.append("LCSC# to verify at order")
    if "verify" in jlc.lower() or "Standard" in jlc:
        flags.append("JLC tier verify/back-side")
    if "OOS" in (mpn+lcsc) or lcsc in ("C143790", "C2803348"):
        flags.append("LCSC retail OOS 2026-07 - alt source")
    row = dict(
        References=",".join(refs_sorted), Qty=len(refs_sorted), Value=value,
        Description=descr, Footprint_intended=fp, MPN=mpn, LCSC=lcsc,
        JLC_Tier=jlc, DNP=dnp, Verify_Flags="; ".join(flags),
    )
    rows.append(row)

# sort rows by first refdes type then number
rows.sort(key=lambda r: refsort(r["References"].split(",")[0]))

cols = ["References", "Qty", "Value", "Description", "Footprint_intended",
        "MPN", "LCSC", "JLC_Tier", "DNP", "Verify_Flags"]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)

total = sum(r["Qty"] for r in rows)
placed = sum(r["Qty"] for r in rows if not r["DNP"])
print(f"wrote {OUT}: {len(rows)} unique lines, {total} parts ({placed} populated, {total-placed} DNP)")
print("unique component refdes count:", len(comps))
