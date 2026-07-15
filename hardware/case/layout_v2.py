"""Loudest Micro Rev A — Layout v2 constants (single source of truth for CAD).

Generated verbatim from the millimetre table in
``docs/independent-design/phase0-layout-v2-notes.md`` (the D1 top-band
re-freeze, which *supersedes* phase0-layout-notes.md). Companion KLE:
``docs/independent-design/layout-v2.json``.

A future layout tweak is a one-file edit here; ``loudest_case.py`` and the
coupons import every board-derived number from this module and never
hard-code a layout dimension.

Coordinate convention (matches the notes):
    origin = PCB top-left corner
    +x     = right   (across the key columns)
    +y     = down    (from the top control band toward the touch row)
    units  = millimetres

The CAD (``loudest_case.py``) maps this straight through with identity in
X/Y (world_x = layout_x, world_y = layout_y) so handedness is preserved —
i.e. the printed case is NOT a mirror image of the PCB. Z (out-of-plane,
+up = toward the keycaps) is added by the CAD with the PCB *top* face at
Z = 0. See that module's header for the Z stack.
"""

# --- Board ---------------------------------------------------------------
# phase0-layout-v2-notes.md "Board" table.
PCB_W = 84.2            # PCB outline width  (x), mm
PCB_H = 103.7           # PCB outline height (y), mm
PCB_CORNER_R = 5.0      # PCB outline corner radius, mm
PCB_THICKNESS = 1.6     # research/04 §1A: JLCPCB standard 1.6 mm
KEY_PITCH = 19.05       # MX 1u pitch, mm (research/04 §1A)

# --- Mounting holes (5× M2) ---------------------------------------------
# phase0-layout-v2-notes.md "Mounting": 5× M2.
# The 4 corners drive the case's M3 lid-fixing bosses (deliverable 1b);
# the 5th (centre) is a PCB-only M2 and is NOT used by the case bosses.
MOUNT_HOLES = [
    (7.0, 7.0),
    (77.2, 7.0),
    (7.0, 96.7),
    (77.2, 96.7),
    (42.1, 42.9),
]
CORNER_MOUNT_HOLES = MOUNT_HOLES[:4]   # the four the case fixes to
CENTER_MOUNT_HOLE = MOUNT_HOLES[4]     # PCB-only M2

# --- Key grid ------------------------------------------------------------
# phase0-layout-v2-notes.md "Element centers" + "Grid math":
#   columns 13.525 / 32.575 / 51.625 / 70.675  (19.05 pitch)
#   rows    33.35  / 52.40  / 71.45  / 90.50    (19.05 pitch)
COL_X = [13.525, 32.575, 51.625, 70.675]
ROW_Y = [33.35, 52.40, 71.45, 90.50]

# SW1-SW4 (row 0), SW5-SW8 (row 1), SW9-SW12 (row 2): 12× 1U keys.
SWITCHES_1U = [(x, y) for y in ROW_Y[0:3] for x in COL_X]

# SW13: 2U key, plate-mount stab, stems ±11.9 (23.8 span).
SWITCH_2U = (42.100, 90.50)
STAB_HALF_SPACING = 11.9   # 2U stab stem offset from centre (notes: ±11.9)

# All 13 switch centres (for per-switch hotswap-socket keep-outs).
ALL_SWITCHES = SWITCHES_1U + [SWITCH_2U]

# --- Top control band + special elements --------------------------------
# phase0-layout-v2-notes.md "Element centers".
JS1_CENTER = (13.525, 13.0)   # planar joystick (Adafruit-444-class), top-left
JS_CAP_D = 11.0               # cap Ø11
JS_TRAVEL_D = 15.0            # travel Ø15  (aperture = travel + clearance)

RE1_CENTER = (70.675, 13.0)   # rotary encoder EC11, top-right
RE1_KNOB_D = 18.0             # knob Ø18 nominal (Ø20 possible if band shifts +1)
RE1_SHAFT_D = 6.0             # EC11 6 mm shaft (research/04 §1C)

USB_CENTER_X = 42.100         # USB-C receptacle centre on the TOP edge (y = 0)
USB_EDGE_Y = 0.0              # top edge

TP1_CENTER = (13.525, 90.50)  # capacitive touch pad, bottom-left
TP1_PAD = 14.0                # 14 × 14 copper pour

LYR_CENTER = (13.525, 82.0)   # layer-indicator LED, top-firing (light pipe)

SVC_CENTER = (70.675, 90.50)  # BOOT + RESET tacts + SWD pads (service zone)
