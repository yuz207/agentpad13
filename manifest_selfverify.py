#!/usr/bin/env python3
"""MANIFEST 9-check self-verification for the release bundle (`release/`).

Run it from anywhere:  python3 manifest_selfverify.py

`release/MANIFEST.md` lists every file in the bundle with its md5 and byte
count.  This script proves that listing is true of the bundle sitting next to
it, so you can confirm nothing was truncated or swapped in transit before you
send a file to a fab.  Nine checks:

  existence, md5, bytes, no-orphans, stats-count-vs-rows, stats-count-vs-disk,
  stats-bytes-vs-rows, stats-bytes-vs-disk, self-exclusion.

"no-orphans" is the direction people forget: it fails if the bundle contains a
file the manifest does not list, so extra content cannot slip in unnoticed.
The on-disk walk deliberately includes dotfiles.

Exit status is 0 only when all nine pass.
"""
import hashlib
import os
import re
import sys

BUNDLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "release")
MANIFEST = os.path.join(BUNDLE, "MANIFEST.md")

ROW_RE = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{32})` \| (\d+) \|", re.M)
STATS_RE = re.compile(r"^## Stats: (\d+) files, [\d.]+ MiB \((\d+) bytes\)", re.M)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    with open(MANIFEST, encoding="utf-8") as fh:
        text = fh.read()

    rows = {}
    for m in ROW_RE.finditer(text):
        rows[m.group(1)] = (m.group(2), int(m.group(3)))

    stats = STATS_RE.search(text)
    if not stats:
        print("FATAL: no '## Stats:' line found in MANIFEST.md")
        return 2
    stats_count, stats_bytes = int(stats.group(1)), int(stats.group(2))

    disk = set()
    for root, _dirs, files in os.walk(BUNDLE):
        for fn in files:
            disk.add(os.path.relpath(os.path.join(root, fn), BUNDLE))
    disk_no_manifest = disk - {"MANIFEST.md"}

    n_rows = len(rows)
    present, md5_ok, bytes_ok = [], [], []
    missing, md5_bad, bytes_bad = [], [], []
    for path, (want_md5, want_bytes) in sorted(rows.items()):
        ap = os.path.join(BUNDLE, path)
        if not os.path.isfile(ap):
            missing.append(path)
            continue
        present.append(path)
        got_md5, got_bytes = md5_of(ap), os.path.getsize(ap)
        (md5_ok if got_md5 == want_md5 else md5_bad).append(
            path if got_md5 == want_md5 else f"{path} row={want_md5} disk={got_md5}"
        )
        (bytes_ok if got_bytes == want_bytes else bytes_bad).append(
            path if got_bytes == want_bytes else f"{path} row={want_bytes} disk={got_bytes}"
        )

    orphans = sorted(disk_no_manifest - set(rows))
    row_sum = sum(b for _, b in rows.values())
    disk_sum = sum(os.path.getsize(os.path.join(BUNDLE, p)) for p in disk_no_manifest)
    self_row = "MANIFEST.md" in rows

    checks = [
        ("existence", not missing,
         f"{len(present)}/{n_rows} listed files present", missing),
        ("md5", not md5_bad,
         f"{len(md5_ok)}/{n_rows} md5 match", md5_bad),
        ("bytes", not bytes_bad,
         f"{len(bytes_ok)}/{n_rows} byte counts match", bytes_bad),
        ("no-orphans", not orphans,
         f"{len(orphans)} on-disk file(s) without a row", orphans),
        ("stats-count-rows", stats_count == n_rows,
         f"Stats {stats_count} vs rows {n_rows}", []),
        ("stats-count-disk", stats_count == len(disk_no_manifest),
         f"Stats {stats_count} vs on-disk {len(disk_no_manifest)}", []),
        ("stats-bytes-rows", stats_bytes == row_sum,
         f"Stats {stats_bytes} vs row-sum {row_sum}", []),
        ("stats-bytes-disk", stats_bytes == disk_sum,
         f"Stats {stats_bytes} vs on-disk-sum {disk_sum}", []),
        ("self-exclusion", not self_row,
         "MANIFEST.md has no self-row" if not self_row else "MANIFEST.md HAS a self-row", []),
    ]

    npass = 0
    for i, (name, ok, detail, offenders) in enumerate(checks, start=1):
        npass += ok
        print(f"[{'PASS' if ok else 'FAIL'}] {i} {name:<19}{detail}")
        if not ok:
            for off in offenders:
                print(f"         -> {off}")
    print(f"RESULT: {npass}/9 checks PASS")
    return 0 if npass == 9 else 1


if __name__ == "__main__":
    sys.exit(main())
