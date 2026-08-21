#!/bin/sh
# Fetch the RP2040 bootrom (B1) dump that ships with rp2040js and convert it
# to CommonJS for the runners. The source and digest are pinned so a clean
# install cannot silently change emulator inputs.
set -eu
cd "$(dirname "$0")"

BOOTROM_URL="https://raw.githubusercontent.com/wokwi/rp2040js/7701ee065f50a04380f81361befd754810cb9e28/demo/bootrom.ts"
BOOTROM_SHA256="99f8a1f813ce3aa9415884de3fb6c5b962d3c6fa0394b05413ad3c7b3c39ec62"
SOURCE_TMP="$(mktemp "${TMPDIR:-/tmp}/agentpad13-bootrom.XXXXXX")"
OUTPUT_TMP="$(mktemp "${TMPDIR:-/tmp}/agentpad13-bootrom-cjs.XXXXXX")"

cleanup() {
    rm -f "$SOURCE_TMP" "$OUTPUT_TMP"
}
trap cleanup EXIT HUP INT TERM

curl -fsSL "$BOOTROM_URL" -o "$SOURCE_TMP"
ACTUAL_SHA256="$(node -e 'const fs=require("fs"); const crypto=require("crypto"); process.stdout.write(crypto.createHash("sha256").update(fs.readFileSync(process.argv[1])).digest("hex"));' "$SOURCE_TMP")"
if [ "$ACTUAL_SHA256" != "$BOOTROM_SHA256" ]; then
    echo "bootrom source digest mismatch" >&2
    exit 1
fi

if [ -L bootrom.cjs ]; then
    echo "refusing to replace symlink: bootrom.cjs" >&2
    exit 1
fi

sed 's/^export //' "$SOURCE_TMP" > "$OUTPUT_TMP"
printf '%s\n' 'module.exports = { bootromB1 };' >> "$OUTPUT_TMP"
mv "$OUTPUT_TMP" bootrom.cjs
echo "bootrom.cjs ready ($(wc -c < bootrom.cjs | tr -d ' ') bytes)"
