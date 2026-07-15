"""Robust S-expression serializer for KiCad 9 files.

Node = list whose [0] is an unquoted keyword; children are:
  - list            -> nested node
  - Raw(str)        -> emitted verbatim (unquoted atom: yes/no, layer names, enums)
  - str             -> quoted string (escaped)
  - int/float       -> number
  - bool            -> yes/no
"""

class Raw(str):
    """Marker: emit verbatim, no quoting."""
    pass

def _num(x):
    if isinstance(x, float):
        s = ("%.6f" % x)
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s if s not in ("", "-0") else "0"
    return str(x)

def dump(node):
    if isinstance(node, Raw):
        return str(node)
    if isinstance(node, bool):
        return "yes" if node else "no"
    if isinstance(node, (int, float)):
        return _num(node)
    if isinstance(node, str):
        return '"' + node.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(node, list):
        head = node[0]
        parts = [str(head)]
        for c in node[1:]:
            parts.append(dump(c))
        return "(" + " ".join(parts) + ")"
    raise TypeError("bad node: %r" % (node,))
