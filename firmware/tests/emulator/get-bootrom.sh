#!/bin/sh
# Fetch the RP2040 bootrom (B1) dump that ships with the rp2040js demos and
# convert it to CommonJS for runner.cjs. Run once before `npm run smoke:*`.
set -eu
cd "$(dirname "$0")"
curl -fsSL https://raw.githubusercontent.com/wokwi/rp2040js/main/demo/bootrom.ts -o bootrom.ts
sed 's/^export //' bootrom.ts > bootrom.cjs
echo "module.exports = { bootromB1 };" >> bootrom.cjs
rm bootrom.ts
echo "bootrom.cjs ready ($(wc -c < bootrom.cjs | tr -d ' ') bytes)"
