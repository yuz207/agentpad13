# Evidence files

`codex-oai-emulator.json` is the current emulator capture for
`release/firmware/prebuilt/agentpad13_codex_oai.uf2`. It was regenerated from
this checkout and must match the UF2 SHA-256 and byte size recorded in
`codex-oai-current-manifest.json`. The current port rebuild is 93,696 bytes
with SHA-256
`fcb50b2419419be43b7cf90b00a96b16063fcaf182bc24b9642d57e2e8adf54d`.

Two earlier provenance layers remain explicit:

- The imported phase-3 migration baseline was 92,160 bytes with SHA-256
  `d1768471eef4d0be12c1fc264279f20b9a7d293ea902c0608ebcfb4643ae35be`.
  It was copied byte-for-byte before the destination rebuild and is superseded
  by the current port artifact; it is not a claim about the final source.
- `codex-oai-manifest.json` is retained as historical full-image evidence for
  the still older 92,672-byte artifact with SHA-256
  `11ee3ed649cf198186fc1e3c190fcaf6a7a1cfbdb18f68ebbead974b09a1712b`.
  Its ELF metrics and hash intentionally refer to that older artifact; it is
  not a claim about the current release UF2.

To produce a new full manifest after a clean QMK build, run
`firmware/tools/verify_codex_oai_artifact.py` with the newly generated ELF, the
current emulator JSON and an output path below this directory. The verifier
checks the UF2 hash, ELF size/symbols and emulator handshake atomically; no
device or removable volume is accessed.
