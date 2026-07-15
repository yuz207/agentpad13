"""KiCad 9 flat-schematic generator (label/coordinate-union connectivity).

Strategy (validated against kicad-happy analyzer net-graph math):
  * Every symbol placed at rotation 0, no mirror -> abs pin = (x+px, y-py).
  * Each pin gets a short horizontal stub wire ending in either a global_label
    (signal net) or a power symbol (power rail). Same-named global labels and
    same-named power symbols union across the sheet -> nets by name.
  * NC pins get a no_connect marker at the pin coordinate.
Geometry is generated from the same pin table used for the lib_symbol, so the
stub/label always lands exactly on the pin's connection point.
"""
import uuid
from sexp import dump, Raw

def U():
    return str(uuid.uuid4())

PITCH = 2.54     # pin-to-pin vertical spacing
PINX  = 6.35     # x of pin connection point (tip); body half-width 3.81 + pin len 2.54
PINLEN = 2.54
STUB  = 5.08     # stub length from pin tip to label
POWER_NETS = {"GND", "+3V3", "+5V", "+1V1", "VBUS", "+VBUS"}

def _eff(size=1.27):
    return ["effects", ["font", ["size", size, size]]]

def _eff_hide(size=1.27):
    return ["effects", ["font", ["size", size, size]], ["hide", Raw("yes")]]

def _instances(project, root_uuid, ref):
    return ["instances", ["project", project,
            ["path", "/" + root_uuid, ["reference", ref], ["unit", 1]]]]

class Schematic:
    def __init__(self, project="loudest", paper="A2"):
        self.project = project
        self.paper = paper
        self.root_uuid = U()
        self.libsyms = {}      # name -> lib node
        self.geom = {}         # name -> {num:(px,py,side)}
        self.body = []         # top-level placed nodes / wires / labels
        self._pwrflag_at = (25.0, 25.0)
        self.refs = set()

    # ---- library symbols ----
    def define_symbol(self, name, pins, is_power=False):
        """pins: list of (num, pinname, etype-str). Left/right auto split."""
        left = pins[0::2]
        right = pins[1::2]
        geom = {}
        sub = ["symbol", name + "_1_1"]
        # KiCad pin (at X Y ANGLE): (X,Y) is the connection point (outer tip);
        # the analyzer uses exactly this for pin-abs = (cx+X, cy-Y). Angle is
        # cosmetic. Left tip at -PINX points right toward body (angle 0);
        # right tip at +PINX points left toward body (angle 180).
        for r, (num, pnm, et) in enumerate(left):
            px, py = -PINX, -r * PITCH
            geom[str(num)] = (px, py, 'L')
            sub.append(["pin", Raw(et), Raw("line"),
                        ["at", px, py, 0], ["length", PINLEN],
                        ["name", str(pnm), _eff(1.0)],
                        ["number", str(num), _eff(1.0)]])
        for r, (num, pnm, et) in enumerate(right):
            px, py = PINX, -r * PITCH
            geom[str(num)] = (px, py, 'R')
            sub.append(["pin", Raw(et), Raw("line"),
                        ["at", px, py, 180], ["length", PINLEN],
                        ["name", str(pnm), _eff(1.0)],
                        ["number", str(num), _eff(1.0)]])
        node = ["symbol", name,
                ["pin_names", ["offset", 0]],
                ["exclude_from_sim", Raw("no")],
                ["in_bom", Raw("yes")], ["on_board", Raw("yes")]]
        if is_power:
            node.insert(2, ["power"])
        node += [
            ["property", "Reference", "U", ["at", 0, PITCH * 2, 0], _eff()],
            ["property", "Value", name.split(":")[-1], ["at", 0, -PITCH * 2, 0], _eff()],
        ]
        # rectangle body (cosmetic) spanning the pin columns
        nrows = max(len(left), len(right))
        top = 1.27
        bot = -(nrows - 1) * PITCH - 1.27 if nrows else -1.27
        if not is_power:
            node.append(["rectangle", ["start", -3.81, top], ["end", 3.81, bot],
                         ["stroke", ["width", 0.254], ["type", Raw("default")]],
                         ["fill", ["type", Raw("none")]]])
        node.append(sub)
        self.libsyms[name] = node
        self.geom[name] = geom

    def define_power_symbol(self, net, etype="power_in"):
        """Power symbol: single pin at local (0,0) so its abs position equals
        the placement coordinate (= the stub endpoint it is dropped on)."""
        name = "power:" + net
        node = ["symbol", name, ["power"], ["pin_names", ["offset", 0]],
                ["exclude_from_sim", Raw("no")], ["in_bom", Raw("yes")],
                ["on_board", Raw("yes")],
                ["property", "Reference", "#PWR", ["at", 0, 0, 0], _eff_hide()],
                ["property", "Value", net, ["at", 0, 3.81, 0], _eff()],
                ["symbol", name + "_0_1",
                 ["pin", Raw(etype), Raw("line"), ["at", 0, 0, 90], ["length", 0],
                  ["name", net, _eff(1.0)], ["number", "1", _eff(1.0)]]]]
        self.libsyms[name] = node
        self.geom[name] = {"1": (0.0, 0.0, 'U')}

    # ---- placement ----
    def place(self, ref, libname, value, x, y, pinmap,
              footprint="", mpn="", lcsc="", jlc="", dnp=False, descr="", extra=None):
        assert libname in self.geom, "undefined symbol %s" % libname
        assert ref not in self.refs, "dup ref %s" % ref
        self.refs.add(ref)
        uid = U()
        node = ["symbol", ["lib_id", libname], ["at", x, y, 0], ["unit", 1],
                ["exclude_from_sim", Raw("no")], ["in_bom", Raw("yes")],
                ["on_board", Raw("yes")], ["dnp", Raw("yes" if dnp else "no")],
                ["uuid", uid],
                ["property", "Reference", ref, ["at", x + 10.16, y - 1.27, 0], _eff()],
                ["property", "Value", value, ["at", x + 10.16, y + 1.27, 0], _eff()]]
        if footprint:
            node.append(["property", "Footprint", footprint, ["at", x, y, 0], _eff_hide()])
        node.append(["property", "Datasheet", "~", ["at", x, y, 0], _eff_hide()])
        if descr:
            node.append(["property", "Description", descr, ["at", x, y, 0], _eff_hide()])
        if mpn:
            node.append(["property", "MPN", mpn, ["at", x, y, 0], _eff_hide()])
        if lcsc:
            node.append(["property", "LCSC", lcsc, ["at", x, y, 0], _eff_hide()])
        if jlc:
            node.append(["property", "JLC", jlc, ["at", x, y, 0], _eff_hide()])
        if extra:
            for k, v in extra.items():
                node.append(["property", k, v, ["at", x, y, 0], _eff_hide()])
        # pin-number -> uuid map (KiCad 9 fidelity so it opens cleanly)
        geom = self.geom[libname]
        for num in geom:
            node.append(["pin", str(num), ["uuid", U()]])
        node.append(_instances(self.project, self.root_uuid, ref))
        self.body.append(node)
        # per-pin stubs + labels
        for num, net in pinmap.items():
            px, py, side = geom[str(num)]
            ax, ay = x + px, y - py
            if net == "NC":
                self.body.append(["no_connect", ["at", ax, ay], ["uuid", U()]])
                continue
            ex = ax - STUB if side == 'L' else ax + STUB
            ey = ay
            self.body.append(["wire", ["pts", ["xy", ax, ay], ["xy", ex, ey]],
                              ["stroke", ["width", 0], ["type", Raw("default")]],
                              ["uuid", U()]])
            self._netmark(net, ex, ey, side)

    def _netmark(self, net, x, y, side):
        if net in POWER_NETS:
            self.body.append(self._power_sym(net, x, y))
        else:
            just = "right" if side == 'L' else "left"
            self.body.append(["global_label", net, ["shape", Raw("input")],
                              ["at", x, y, 0 if side == 'R' else 180],
                              ["effects", ["font", ["size", 1.27, 1.27]],
                               ["justify", Raw(just)]],
                              ["uuid", U()]])

    def _power_sym(self, net, x, y):
        return ["symbol", ["lib_id", "power:" + net], ["at", x, y, 0], ["unit", 1],
                ["exclude_from_sim", Raw("no")], ["in_bom", Raw("yes")],
                ["on_board", Raw("yes")], ["dnp", Raw("no")], ["uuid", U()],
                ["property", "Reference", "#PWR", ["at", x, y + 2.54, 0], _eff_hide()],
                ["property", "Value", net, ["at", x, y - 2.54, 0], _eff()],
                _instances(self.project, self.root_uuid, "#PWR?")]

    def add_pwr_flag(self, net, x, y):
        """Place a power symbol for `net` and a PWR_FLAG at the same coord."""
        self.body.append(self._power_sym(net, x, y))
        self.body.append(
            ["symbol", ["lib_id", "power:PWR_FLAG"], ["at", x, y, 0], ["unit", 1],
             ["exclude_from_sim", Raw("no")], ["in_bom", Raw("yes")],
             ["on_board", Raw("yes")], ["dnp", Raw("no")], ["uuid", U()],
             ["property", "Reference", "#FLG", ["at", x, y + 2.54, 0], _eff_hide()],
             ["property", "Value", "PWR_FLAG", ["at", x, y, 0], _eff()],
             _instances(self.project, self.root_uuid, "#FLG?")])

    def note(self, text, x, y):
        self.body.append(["text", text, ["at", x, y, 0],
                          ["effects", ["font", ["size", 1.6, 1.6]], ["justify", Raw("left")]],
                          ["uuid", U()]])

    # ---- output ----
    def dumps(self, title="Loudest Micro Rev A", rev="A-draft"):
        out = ["(kicad_sch",
               "  " + dump(["version", 20250114]),
               "  " + dump(["generator", "loudest_gen"]),
               "  " + dump(["generator_version", "9.0"]),
               "  " + dump(["uuid", self.root_uuid]),
               "  " + dump(["paper", self.paper]),
               "  " + dump(["title_block", ["title", title], ["rev", rev],
                            ["company", "Loudest Micro (open hardware, CERN-OHL-W v2)"],
                            ["comment", 1, "DRAFT - pending human review; footprints bound at layout"]]),
               "  (lib_symbols"]
        for name in sorted(self.libsyms):
            out.append("    " + dump(self.libsyms[name]))
        out.append("  )")
        for n in self.body:
            out.append("  " + dump(n))
        out.append("  " + dump(["sheet_instances", ["path", "/", ["page", "1"]]]))
        out.append(")")
        return "\n".join(out) + "\n"
