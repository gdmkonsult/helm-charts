#!/usr/bin/env bash
# Static upgrade simulation: renders the previous released version of each chart
# (latest git tag <chart>-X.Y.Z) and the working tree, then fails if
#   1. a stateful resource that was a plain release member disappears from the
#      plain manifest — Helm deletes it on upgrade (this deleted 14 prod DBs in
#      eneo 1.0.186 when Cluster/Secret/ConfigMap became hooks), or
#   2. a CNPG Cluster lacks helm.sh/resource-policy: keep.
#
# Usage: ./scripts/check-upgrade-safety.sh [chart-dir]...
set -uo pipefail

STATEFUL='Cluster|PersistentVolumeClaim|StatefulSet|Secret|ObjectStore|ScheduledBackup'
charts=("$@"); [[ ${#charts[@]} -eq 0 ]] && charts=(charts/*)
fail=0

render() { helm template "$1" "$2" --set global.domain=upgradecheck.invalid 2>/dev/null; }

# Prints "Kind/name" for plain (non-hook) resources, one per line.
plain_resources() {
  python3 -c '
import re, sys
for d in sys.stdin.read().split("\n---\n"):
    if re.search(r"helm\.sh/hook[\"\x27]?\s*:", d): continue
    k = re.search(r"^kind: (\w+)", d, re.M); n = re.search(r"^  name: (\S+)", d, re.M)
    if k and n: print(f"{k.group(1)}/{n.group(1)}")'
}

for chart in "${charts[@]}"; do
  [[ -f "$chart/Chart.yaml" ]] || continue
  name=$(basename "$chart")
  cur=$(render "$name" "$chart") || { echo "SKIP $name: helm template failed"; continue; }

  # Rule 2: every CNPG Cluster must carry resource-policy keep.
  missing_keep=$(python3 -c '
import re, sys
for d in sys.stdin.read().split("\n---\n"):
    if re.search(r"^apiVersion: postgresql\.cnpg\.io/", d, re.M) and re.search(r"^kind: Cluster$", d, re.M) \
       and not re.search(r"helm\.sh/resource-policy[\"\x27]?\s*:\s*[\"\x27]?keep", d):
        print("  " + re.search(r"^  name: (\S+)", d, re.M).group(1))' <<<"$cur")
  if [[ -n "$missing_keep" ]]; then
    echo "FAIL $name: CNPG Cluster without helm.sh/resource-policy: keep"; echo "$missing_keep"; fail=1
  fi

  # Rule 1: compare against the previous released version.
  version=$(awk '/^version:/{print $2}' "$chart/Chart.yaml")
  prev_tag=$(git tag -l "$name-*" --sort=-v:refname | grep -vx "$name-$version" | head -1)
  if [[ -z "$prev_tag" ]]; then echo "OK   $name (no previous tag)"; continue; fi
  tmp=$(mktemp -d)
  git archive "$prev_tag" "charts/$name" | tar -x -C "$tmp"
  prev=$(render "$name" "$tmp/charts/$name"); rm -rf "$tmp"
  [[ -n "$prev" ]] || { echo "SKIP $name: could not render $prev_tag"; continue; }

  dropped=$(comm -23 <(plain_resources <<<"$prev" | sort -u) <(plain_resources <<<"$cur" | sort -u) | grep -E "^($STATEFUL)/" || true)
  if [[ -n "$dropped" ]]; then
    echo "FAIL $name: upgrading from $prev_tag would DELETE these stateful resources:"
    sed 's/^/  /' <<<"$dropped"
    echo "  (they left the plain manifest — renamed, gated off by default, or turned into hooks)"
    fail=1
  elif [[ -z "$missing_keep" ]]; then
    echo "OK   $name (vs $prev_tag)"
  fi
done
exit $fail
