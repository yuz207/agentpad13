"""Read module-level constants out of a Python source file WITHOUT importing it.

`agentpad13_case_v2.py` cannot be imported here: it needs build123d/OCP and it
parses a banked `v5_6.kicad_pcb` that does not exist at that path in the
reorganised repo (`agentpad13_case_v2.py:260-262`, `:292`). Importing it would
also run its gates. So the constants are read statically, which additionally
gives us the exact line number of every value for the `sources` citations.

Only literals and arithmetic over already-known names are evaluated; anything
else (calls, comprehensions, attribute access) is refused rather than guessed.
"""

from __future__ import annotations

import ast
from pathlib import Path


class ConstError(RuntimeError):
    pass


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


class SourceConstants:
    """Module-level constants of one source file, with line provenance."""

    def __init__(self, path: Path, repo_root: Path, seed: dict | None = None):
        self.path = Path(path)
        self.rel = str(self.path.relative_to(repo_root))
        self._src = self.path.read_text(encoding="utf-8")
        self._tree = ast.parse(self._src, filename=str(self.path))
        self._nodes: dict[str, ast.AST] = {}
        self._lines: dict[str, int] = {}
        self._cache: dict[str, object] = dict(seed or {})
        self._seeded = set(self._cache)
        for node in self._tree.body:  # module level only -- no nested scopes
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t for t in node.targets]
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
            for tgt in targets:
                if isinstance(tgt, ast.Name):
                    self._nodes[tgt.id] = node.value
                    self._lines[tgt.id] = node.lineno
                elif isinstance(tgt, ast.Tuple):  # a, b = expr  (e.g. PCB_W, PCB_H)
                    for i, el in enumerate(tgt.elts):
                        if isinstance(el, ast.Name):
                            self._nodes[el.id] = ("__unpack__", node.value, i)
                            self._lines[el.id] = node.lineno

    # -- public ----------------------------------------------------------
    def line(self, name: str) -> int:
        if name not in self._lines:
            raise ConstError(f"{name!r} not assigned at module level in {self.rel}")
        return self._lines[name]

    def cite(self, name: str, note: str = "") -> str:
        """`release/...py:348` (+ optional note) -- the provenance string."""
        base = f"{self.rel}:{self.line(name)}"
        return f"{base} ({note})" if note else base

    def get(self, name: str):
        if name in self._cache:
            return self._cache[name]
        if name not in self._nodes:
            raise ConstError(f"{name!r} not assigned at module level in {self.rel}")
        node = self._nodes[name]
        if isinstance(node, tuple) and node and node[0] == "__unpack__":
            seq = self._eval(node[1], name)
            if not isinstance(seq, (list, tuple)):
                raise ConstError(f"{name!r}: unpack source is not a sequence")
            val = seq[node[2]]
        else:
            val = self._eval(node, name)
        self._cache[name] = val
        return val

    def many(self, *names: str) -> tuple:
        return tuple(self.get(n) for n in names)

    def source_line(self, name: str) -> str:
        return self._src.splitlines()[self.line(name) - 1].rstrip()

    # -- internals -------------------------------------------------------
    def _eval(self, node, owner: str):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float, str, bool)) or node.value is None:
                return node.value
            raise ConstError(f"{owner!r}: unsupported constant {node.value!r}")
        if isinstance(node, ast.Name):
            return self.get(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval(node.operand, owner)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd):
            return +self._eval(node.operand, owner)
        if isinstance(node, ast.BinOp):
            fn = _BINOPS.get(type(node.op))
            if fn is None:
                raise ConstError(f"{owner!r}: unsupported operator {type(node.op).__name__}")
            return fn(self._eval(node.left, owner), self._eval(node.right, owner))
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(self._eval(e, owner) for e in node.elts)
        raise ConstError(
            f"{owner!r} in {self.rel} is not a literal/arithmetic expression "
            f"({type(node).__name__}) -- read it by hand and cite it, do not guess."
        )
