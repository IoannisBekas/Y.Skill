#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="${1:-$root/dist/project-health-pass.zip}"

mkdir -p "$(dirname "$out")"
rm -f "$out"

(
  cd "$root/skills"
  zip -qr "$out" project-health-pass
)

echo "Wrote $out"
