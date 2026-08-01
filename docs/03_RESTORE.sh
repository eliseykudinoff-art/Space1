#!/bin/bash
# Restore 03_PIPELINE_MATH.md v1.3 from base64-gzip halves
set -e
cd "$(dirname "$0")/.."
if [[ -f docs/03_PIPELINE_MATH.md.gz.b64 ]]; then
  base64 -d docs/03_PIPELINE_MATH.md.gz.b64 | gunzip > 03_PIPELINE_MATH.md
elif [[ -f docs/03_b64_a.txt && -f docs/03_b64_b.txt ]]; then
  cat docs/03_b64_a.txt docs/03_b64_b.txt | base64 -d | gunzip > 03_PIPELINE_MATH.md
else
  echo "Missing encoded parts"; exit 1
fi
echo "Restored 03_PIPELINE_MATH.md ($(wc -c < 03_PIPELINE_MATH.md) bytes)"
# expected SHA256 prefix: 896a08c6053ee07d
