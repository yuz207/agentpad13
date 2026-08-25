"""work-loudest v5 toppers — RENDER SHEETS for the v2 family.

    /Users/yuanz/.local/share/uv/tools/cad-khana/bin/python render_toppers_v2.py

Writes ./renders/toppers_v2_*.png.

TWO RULES THIS RENDERER EXISTS TO OBEY.

1.  THE PARTS ARE READ BACK FROM THE EXPORTED STL BYTES, never from the
    in-memory solid.  What the owner judges is therefore literally what the
    slicer will read — including the export mirror.  Knob A's helix is
    chiral, so a render made from the solid instead of the file would show
    the WRONG HAND and nobody would know.

2.  It is a z-buffered software rasteriser, not matplotlib.  matplotlib sorts
    whole polygons, so it would mis-composite exactly the interpenetration
    these images exist to test (a topper at full tilt against a keycap).

FRAMES.  The STL files are in the PRINT frame (the design frame mirrored
about XZ — see topper_frame_v2.export_print_frame).  Part-alone panels are
drawn AS EXPORTED, so the helix hand shown is the hand that prints.  On-deck
panels mirror the triangles back into the design frame so the case context
(keycaps at +y, the plate opening offset in +x) is right; that mirror is a
measured no-op for the nub and the puck and cosmetic for a rotary knob.

The keycaps are drawn at their TRUE STEM-INSERTED geometry: bottom rim
+11.6, dish top +17.6 — not the naive cap-on-switch +21.2.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import encoder_knob_v2 as K
import stick_topper_v2 as S
import topper_frame_v2 as F

HERE = os.path.dirname(os.path.abspath(__file__))
RDIR = os.path.join(HERE, "renders")
os.makedirs(RDIR, exist_ok=True)

SS = 2                       # supersampling
FONTS = ["/System/Library/Fonts/Supplemental/Arial.ttf",
         "/System/Library/Fonts/Helvetica.ttc"]

COL_PLATE = (198, 203, 210)
COL_KNOB = (231, 233, 237)
COL_NUB = (58, 60, 66)
COL_TPU = (46, 48, 54)
COL_KEY = (214, 217, 223)
COL_MOD = (146, 150, 158)
COL_SHAFT = (170, 174, 182)
COL_GHOST = (206, 150, 150)
INK = (24, 24, 28)
RED = (186, 44, 44)
GRN = (22, 116, 56)
BLU = (40, 62, 194)


def font(sz):
    for p in FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except OSError:
                pass
    return ImageFont.load_default()


# ------------------------------------------------------------------ meshes
def load_stl(path):
    """Binary STL -> (n, 3, 3) vertex array.  THE POINT OF THIS RENDERER."""
    return F.read_stl_triangles(path)


def tess(shape, tol=0.02, ang=0.2):
    """Scene props only (deck, keycaps, module) — never the toppers."""
    v, f = shape.tessellate(tolerance=tol, angular_tolerance=ang)
    return np.array([[p.X, p.Y, p.Z] for p in v], float)[np.array(f, int)]


def mirror_y(t):
    """Print frame <-> design frame."""
    out = t.copy()
    out[:, :, 1] *= -1.0
    return out[:, ::-1, :]          # keep the winding outward


def move(t, dx=0.0, dy=0.0, dz=0.0):
    return t + np.array([dx, dy, dz], float)


def spin(t, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    m = np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])
    return t @ m.T


def tilt(t, deg, pivot_z=F.PIVOT_Z):
    """Rigid tilt about the gimbal pivot, toward +y (toward SW4)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    o = t - np.array([0.0, 0.0, pivot_z])
    y = o[:, :, 1] * c + o[:, :, 2] * s
    z = -o[:, :, 1] * s + o[:, :, 2] * c
    out = o.copy()
    out[:, :, 1], out[:, :, 2] = y, z
    return out + np.array([0.0, 0.0, pivot_z])


# -------------------------------------------------------------- rasteriser
def render(parts, eye, target, up=(0, 0, 1), w=760, h=600, fov=None,
           ortho_h=None, bg=(248, 249, 251)):
    """parts = [(tris Nx3x3, rgb)].  fov -> perspective, ortho_h -> ortho."""
    W, H = w * SS, h * SS
    eye = np.array(eye, float)
    fwd = np.array(target, float) - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, np.array(up, float))
    right /= np.linalg.norm(right)
    upv = np.cross(right, fwd)
    M = np.stack([right, upv, -fwd])

    zbuf = np.full((H, W), np.inf)
    img = np.zeros((H, W, 3), float) + np.array(bg, float) / 255.0
    L1 = np.array([0.40, -0.58, 0.71])
    L1 /= np.linalg.norm(L1)
    L2 = np.array([-0.62, 0.30, 0.42])
    L2 /= np.linalg.norm(L2)

    for tri, col in parts:
        if len(tri) == 0:
            continue
        col = np.array(col, float) / 255.0
        cam = ((tri.reshape(-1, 3) - eye) @ M.T).reshape(-1, 3, 3)
        depth = -cam[:, :, 2]
        if fov is not None:
            f = (H / 2) / math.tan(math.radians(fov) / 2)
            d = np.maximum(depth, 1e-6)
            sx = W / 2 + f * cam[:, :, 0] / d
            sy = H / 2 - f * cam[:, :, 1] / d
        else:
            s = H / ortho_h
            sx = W / 2 + s * cam[:, :, 0]
            sy = H / 2 - s * cam[:, :, 1]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(nrm, axis=1, keepdims=True)
        nrm = nrm / np.where(ln < 1e-12, 1.0, ln)
        sh = np.clip(0.34 + 0.48 * np.clip(nrm @ L1, 0, 1)
                     + 0.18 * np.clip(nrm @ L2, 0, 1), 0.0, 1.0)
        face = np.clip(col[None, :] * sh[:, None], 0, 1)
        for k in range(len(tri)):
            x0, x1, x2 = sx[k]
            y0, y1, y2 = sy[k]
            d0, d1, d2 = depth[k]
            if min(d0, d1, d2) <= 0:
                continue
            xmin = max(int(min(x0, x1, x2)), 0)
            xmax = min(int(max(x0, x1, x2)) + 2, W)
            ymin = max(int(min(y0, y1, y2)), 0)
            ymax = min(int(max(y0, y1, y2)) + 2, H)
            if xmax <= xmin or ymax <= ymin:
                continue
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-12:
                continue
            gx, gy = np.meshgrid(np.arange(xmin, xmax) + 0.5,
                                 np.arange(ymin, ymax) + 0.5)
            l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / den
            l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / den
            l2 = 1.0 - l0 - l1
            m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not m.any():
                continue
            z = l0 * d0 + l1 * d1 + l2 * d2
            sub = zbuf[ymin:ymax, xmin:xmax]
            hit = m & (z < sub)
            if not hit.any():
                continue
            sub[hit] = z[hit]
            img[ymin:ymax, xmin:xmax][hit] = face[k]
    out = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(out).resize((w, h), Image.LANCZOS)


def caption(im, lines, size=14, pad=7, col=INK, bottom=False):
    d = ImageDraw.Draw(im)
    fnt = font(size)
    y = (im.size[1] - pad - len(lines) * (size + 3)) if bottom else pad
    for ln, c in lines:
        d.text((pad, y), ln, font=fnt, fill=c or col)
        y += size + 3
    return im


def sheet(images, cols, out, title):
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    th = 34
    im = Image.new("RGB", (cols * w, rows * h + th), (255, 255, 255))
    ImageDraw.Draw(im).text((12, 9), title, font=font(19), fill=INK)
    for i, p in enumerate(images):
        im.paste(p, ((i % cols) * w, th + (i // cols) * h))
    path = os.path.join(RDIR, out)
    im.save(path)
    print(f"wrote renders/{out}  {im.size[0]}x{im.size[1]}")
    return path


# ------------------------------------------------------------- scene props
def deck_patch(cx, cy, half=27.0):
    from build123d import Box, Pos
    return tess(Pos(cx, cy, (F.PLATE_BOT_Z + F.DECK_Z) / 2)
                * Box(2 * half, 2 * half, F.DECK_Z - F.PLATE_BOT_Z))


def keycap(x, y, top_z=F.KEYCAP_TOP_DISH_Z):
    """A keycap at its TRUE stem-inserted height: rim +11.6, top +17.6."""
    from build123d import Box, Pos, Sphere
    h = top_z - F.KEYCAP_RIM_Z
    body = Pos(x, y, F.KEYCAP_RIM_Z + h / 2) * Box(F.KEYCAP_W, F.KEYCAP_W, h)
    a, dd = F.KEYCAP_W / 2 - 1.1, 0.9
    R = (a * a + dd * dd) / (2 * dd)
    body -= Pos(x, y, top_z + R - dd) * Sphere(R)
    return tess(body)


def js_blade():
    """The measured 1.70 x 1.00 blade the topper presses onto, +11.0..+18.4.
    Built in LOCAL coords so it can be tilted with the gimbal exactly like
    the topper it carries — a vertical blade under a tilted cap would be a
    lie, and this renderer exists to catch that class of thing."""
    from build123d import Box, Pos
    return tess(Pos(0, 0, (F.FRAME_TOP_Z + F.BLADE_TIP_Z) / 2)
                * Box(S.SHAFT_LONG, S.SHAFT_SHORT,
                      F.BLADE_TIP_Z - F.FRAME_TOP_Z))


def js_module(seat_z=F.FRAME_TOP_Z):
    """The joystick can, drawn with its top face at the measured frame top."""
    from build123d import Box, Pos
    return tess(Pos(F.JS1_X, F.JS1_Y, seat_z - 3.0) * Box(13.0, 13.0, 6.0))


def enc_shaft():
    from build123d import Box, Circle, Plane, Pos, extrude
    bush = Pos(F.RE1_X, F.RE1_Y, F.Z_BODY_TOP) * extrude(
        Plane.XY * Circle(F.BUSHING_D / 2), amount=F.ENC_BUSHING_LEN)
    sh = Pos(F.RE1_X, F.RE1_Y, F.Z_BUSHING_TOP) * extrude(
        Plane.XY * Circle(F.SHAFT_ROUND_D / 2),
        amount=F.Z_SHAFT_TIP - F.Z_BUSHING_TOP)
    off = F.SHAFT_FLAT_ACROSS - F.SHAFT_ROUND_D / 2
    sh -= Pos(F.RE1_X, F.RE1_Y + off + 2.0,
              (F.Z_FLAT_START + F.Z_SHAFT_TIP) / 2) * Box(
                  8, 4, F.Z_SHAFT_TIP - F.Z_FLAT_START)
    return tess(bush + sh)


# ------------------------------------------------------------------ panels
def part_panel(tris, col, label, extra=(), elev=22.0, azim=-52.0, span=26.0,
               cz=17.5):
    """One topper alone, AS EXPORTED, on a neutral ground."""
    e = math.radians(elev)
    a = math.radians(azim)
    d = 150.0
    eye = (d * math.cos(e) * math.cos(a), d * math.cos(e) * math.sin(a),
           cz + d * math.sin(e))
    im = render([(tris, col)] + list(extra), eye, (0, 0, cz), ortho_h=span)
    return caption(im, label)


def deck_panel(parts, label, target, elev=20.0, azim=-64.0, span=58.0,
               dist=260.0):
    e = math.radians(elev)
    a = math.radians(azim)
    eye = (target[0] + dist * math.cos(e) * math.cos(a),
           target[1] + dist * math.cos(e) * math.sin(a),
           target[2] + dist * math.sin(e))
    return caption(render(parts, eye, target, ortho_h=span), label)


def top_panel(tris, col, label, span=24.0, cxy=(0.0, 0.0), cz=19.0,
              extra=()):
    eye = (cxy[0], cxy[1] - 0.001, cz + 140.0)
    im = render([(tris, col)] + list(extra), eye, (cxy[0], cxy[1], cz),
                ortho_h=span)
    return caption(im, label)


def elev_panel(tris, col, label, span=26.0, cz=17.5, zlines=(), w=760,
               h=600):
    """TRUE side elevation with the eye ON THE +X AXIS.

    That camera is chosen, not aesthetic.  With eye = (+D, 0, cz) and
    up = +z, screen-right is exactly +y and screen-up is exactly +z, and the
    near face of the barrel is the one at x = +R.  A point on that face at
    azimuth th has y = R*sin(th) ~ R*th, so screen-x grows with th:

        a RIGHT-handed helix (th rising with z) runs UP-TO-THE-RIGHT
        a LEFT-handed  helix                    runs UP-TO-THE-LEFT

    So the render and the STL phase-clustering gate can be checked against
    each other by eye, which is the whole point of the panel."""
    D = 200.0
    im = render([(tris, col)], (D, 0.0, cz), (0.0, 0.0, cz), ortho_h=span,
                w=w, h=h)
    d = ImageDraw.Draw(im)
    fnt = font(12)
    s = h / span
    for z, txt, c in zlines:
        y = h / 2 - (z - cz) * s
        d.line([(6, y), (w - 6, y)], fill=c, width=1)
        d.text((8, y - 15), txt, font=fnt, fill=c)
    return caption(im, label, bottom=True)


# ==========================================================================
if __name__ == "__main__":
    stl = os.path.join(HERE, "stl")
    kA = load_stl(os.path.join(stl, "knob_v2_A_clearance_low.stl"))
    kB2 = load_stl(os.path.join(stl, "knob_v2_B2_clearance_low.stl"))
    kC = load_stl(os.path.join(stl, "knob_v2_C_clearance_low.stl"))
    nub = load_stl(os.path.join(stl, "stick_nub_v2_C2_clearance_low.stl"))
    puck = load_stl(os.path.join(stl, "stick_puck_v2_TPU_clearance_low.stl"))
    for nm, t in (("knobA", kA), ("knobB2", kB2), ("knobC", kC),
                  ("nub", nub), ("puck", puck)):
        print(f"  read {nm:6s} {len(t):7d} triangles from the STL bytes")

    # ---------------------------------------------------------- knob sheet
    ims = []
    ZL = [(K.TEX_START_Z, "+18.2", BLU), (K.KNOB_TOP, "+27.0", GRN)]
    for t, tag, note in ((kA, "A", "helical knurl  N=32 @ 30 deg"),
                         (kB2, "B2", "scoop  rim +18.200, cove R12.265"),
                         (kC, "C", "cross-hatch  16+16 @ +/-45 deg")):
        ims.append(part_panel(
            t, COL_KNOB,
            [(f"Knob {tag} — {note}", None),
             ("AS EXPORTED. straight o17.5 body, no skirt, +8.0..+27.0",
              (90, 92, 98))]))
        hand = ([("HANDEDNESS: grooves run UP-TO-THE-LEFT on the near face",
                  RED),
                 ("= a LEFT-handed helix, which is what the STL phase gate "
                  "measured", RED)] if tag == "A" else
                [("both families visible; the pattern is XZ-symmetric",
                  (90, 92, 98))] if tag == "C" else
                [("the notch lands ON +18.2; scoop faces -y in the print "
                  "frame", (90, 92, 98))])
        ims.append(elev_panel(
            t, COL_KNOB,
            [(f"Knob {tag} — TRUE side elevation, eye on the +x axis", None),
             ("screen-right is exactly +y, screen-up is exactly +z;  "
              "lines: +18.2 knurl/scoop line, +27.0 top", (90, 92, 98))]
            + hand,
            span=23.0, cz=17.5, zlines=ZL))
    sheet(ims, 2, "toppers_v2_knobs.png",
          "work-loudest v5 — ENCODER KNOBS v2  (straight o17.5 body, top +27.0, "
          "texture/scoop above +18.2)  — rendered FROM THE EXPORTED STL BYTES")

    # -------------------------------------------------- B2 before / after
    from build123d import export_stl
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        prev = os.path.join(td, "b2_prev.stl")
        export_stl(F.export_print_frame(
            K.knobB2(ridge_y=1.425, rim_z=23.061, yc=8.5)[0]), prev)
        b2_prev = load_stl(prev)
    ims = []
    for t, ttl in ((b2_prev, "BEFORE — v2 study B2: rim +23.061, "
                             "chord 26.0 deg, sagitta 0.06"),
                   (kB2, "AFTER — shipped B2: rim +18.200, chord 48.3 deg, "
                         "sagitta 1.447")):
        ims.append(part_panel(t, COL_KNOB, [(ttl, None),
                                            ("viewed INTO the cove",
                                             (90, 92, 98))],
                              elev=30.0, azim=-104.0, span=25.0, cz=20.0))
    ZLB = [(K.TEX_START_Z, "+18.2", BLU), (23.061, "+23.06", RED),
           (K.KNOB_TOP, "+27.0", GRN)]
    for t, ttl in ((b2_prev, "BEFORE — notch sits at +23.061, 4.861 mm too "
                             "high"),
                   (kB2, "AFTER — notch lands ON the +18.2 knurl line = the "
                         "plateau keycap top")):
        ims.append(elev_panel(t, COL_KNOB,
                              [(ttl, None),
                               ("TRUE side elevation, eye on the +x axis; "
                                "lines: +18.2 knurl line, +23.06 the OLD "
                                "notch, +27.0 top", (90, 92, 98))],
                              span=23.0, cz=17.5, zlines=ZLB))
    sheet(ims, 2, "toppers_v2_knobB2_before_after.png",
          "work-loudest v5 — KNOB B2 SCOOP, REVISED  (owner: 'not concave "
          "enough ... the notch is too high')")

    # ------------------------------------------------------- knobs on deck
    ims = []
    deck = deck_patch(F.RE1_X + 4, F.RE1_Y + 9)
    caps = np.vstack([keycap(F.SW1_X, F.SW1_Y),
                      keycap(F.SW1_X + 19.05, F.SW1_Y)])
    for t, tag in ((kA, "A"), (kB2, "B2"), (kC, "C")):
        d = move(mirror_y(t), F.RE1_X, F.RE1_Y, 0.0)
        ims.append(deck_panel(
            [(deck, COL_PLATE), (caps, COL_KEY), (d, COL_KNOB)],
            [(f"Knob {tag} on the deck, beside REAL stem-inserted keycaps",
              None),
             ("knob top +27.0 stands +9.4 over the dish caps (+17.6)", GRN),
             ("design frame (STL mirrored back) so the case context is right",
              (90, 92, 98))],
            (F.RE1_X + 3, F.RE1_Y + 10, 15.0)))
    ims.append(deck_panel(
        [(deck, COL_PLATE), (caps, COL_KEY), (enc_shaft(), COL_SHAFT)],
        [("the Alps EC11E H20 shaft the bore has to swallow", None),
         ("bushing o7 to +11.5, round o6 to +14.5, flat to the tip +24.5",
          (90, 92, 98)),
         ("knob roof +25.5 -> headroom +1.000", GRN)],
        (F.RE1_X + 3, F.RE1_Y + 10, 15.0)))
    sheet(ims, 2, "toppers_v2_knobs_on_deck.png",
          "work-loudest v5 — ENCODER KNOBS v2 ON THE DECK  (keycaps drawn at "
          "their TRUE inserted height: rim +11.6, top +17.6)")

    # -------------------------------------------------------- stick sheet
    ims = []
    ims.append(part_panel(nub, COL_NUB,
                          [("Nub C2 — o6.189, seven o0.9 x 0.35 dimples",
                            None),
                           ("AS EXPORTED. clears SW4 at the FULL 30 deg",
                            (90, 92, 98))],
                          span=13.0, cz=17.0))
    ims.append(top_panel(nub, COL_NUB,
                         [("Nub C2 — top down, the seven-dot micro-grip",
                           None)], span=9.0, cz=19.6))
    ims.append(part_panel(puck, COL_TPU,
                          [("TPU puck — round o6.350, one piece, cup + "
                            "RAISED X-dashes", None),
                           ("AS EXPORTED. dash tops are "
                            "proud of the cup at +19.6", (90, 92, 98))],
                          span=15.0, cz=17.0))
    ims.append(part_panel(puck, COL_TPU,
                          [("TPU puck — near-top view of the cup and the "
                            "four RAISED dashes", None),
                           ("a true 90 deg top-down washes a 0.40 mm cup "
                            "out; 68 deg shades it", (90, 92, 98)),
                           ("pad 0.30 deep; deepest floor 0.40 "
                            "(minimum roof 0.800)", (90, 92, 98))],
                          elev=68.0, azim=-58.0, span=12.0, cz=18.6))
    sheet(ims, 2, "toppers_v2_stick.png",
          "work-loudest v5 — JOYSTICK TOPPERS v2  (nub C2 + one-piece TPU "
          "puck)  — rendered FROM THE EXPORTED STL BYTES")

    # ----------------------------- both joystick toppers at rest and full throw
    deck2 = deck_patch(F.JS1_X - 4, F.JS1_Y + 9)
    caps2 = np.vstack([keycap(F.SW4_X, F.SW4_Y),
                       keycap(F.SW4_X - 19.05, F.SW4_Y)])
    p_des = mirror_y(puck)
    p_at = move(p_des, F.JS1_X, F.JS1_Y, 0.0)
    p_tilt = move(tilt(p_des, F.TILT_FULL), F.JS1_X, F.JS1_Y, 0.0)
    n_at = move(mirror_y(nub), F.JS1_X, F.JS1_Y, 0.0)
    n_tilt = move(tilt(mirror_y(nub), F.TILT_FULL), F.JS1_X, F.JS1_Y, 0.0)
    can = js_module()
    bl = js_blade()
    blade = move(bl, F.JS1_X, F.JS1_Y, 0.0)
    blade_puck_30 = move(tilt(bl, F.TILT_FULL), F.JS1_X, F.JS1_Y, 0.0)
    blade_30 = move(tilt(bl, F.TILT_FULL), F.JS1_X, F.JS1_Y, 0.0)
    tgt = (F.JS1_X - 2, F.JS1_Y + 9, 14.0)
    ims = [
        deck_panel([(deck2, COL_PLATE), (caps2, COL_KEY), (can, COL_MOD), (blade, COL_SHAFT),
                    (p_at, COL_TPU)],
                   [("TPU puck AT REST", None),
                    ("bottom +14.4 clears the +11.0 frame top by 3.4 mm", GRN)], tgt),
        deck_panel([(deck2, COL_PLATE), (caps2, COL_KEY), (can, COL_MOD), (blade_puck_30, COL_SHAFT),
                    (p_tilt, COL_TPU)],
                   [("TPU puck at the FULL 30 deg, toward SW4", None),
                    ("no restrictor; solid body except for the blade socket",
                     (90, 92, 98))], tgt),
        deck_panel([(deck2, COL_PLATE), (caps2, COL_KEY), (can, COL_MOD), (blade, COL_SHAFT),
                    (n_at, COL_NUB)],
                   [("Nub C2 at rest", None)], tgt),
        deck_panel([(deck2, COL_PLATE), (caps2, COL_KEY), (can, COL_MOD), (blade_30, COL_SHAFT),
                    (n_tilt, COL_NUB)],
                   [("Nub C2 at the FULL 30 deg, toward SW4 — no restrictor",
                     None),
                    ("SW4 clearance +0.2508; contact would be on the cap's "
                     "side wall", GRN),
                    ("at z' 16.071, INSIDE the inserted band 11.6..17.6",
                     (90, 92, 98))], tgt)]
    sheet(ims, 2, "toppers_v2_stick_on_deck.png",
          "JOYSTICK TOPPERS v2 — REST / FULL 30 deg, beside inserted keycaps")

    # ------------------------------------------------------------- hero
    deck3 = deck_patch(42.0, 22.0, half=50.0)
    caps3 = np.vstack([keycap(x, y)
                       for y in (F.SW1_Y,)
                       for x in (13.525, 32.575, 51.625, 70.675)])
    hero = [(deck3, COL_PLATE), (caps3, COL_KEY),
            (move(mirror_y(kA), F.RE1_X, F.RE1_Y, 0.0), COL_KNOB),
            (move(mirror_y(puck), F.JS1_X, F.JS1_Y, 0.0), COL_TPU)]
    im = deck_panel(hero,
                    [("agentpad13 v2 toppers — the hierarchy", None),
                     ("knob +27.0  |  keycaps +17.6  |  puck +19.6", GRN)],
                    (42.0, 20.0, 14.0), elev=17.0, azim=-70.0, span=104.0,
                    dist=420.0)
    sheet([im], 1, "toppers_v2_family_hero.png",
          "work-loudest v5 — TOPPER FAMILY v2 ON THE DECK")
    print("done")
