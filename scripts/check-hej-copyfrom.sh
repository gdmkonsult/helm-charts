#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
rendered=$(mktemp)
trap 'rm -f "$rendered"' EXIT

helm template hej-test "$root/charts/hej" \
  --set global.domain=hej-test.example.invalid \
  --set testEnvironment=true \
  --set copyFrom.enabled=true \
  --set copyFrom.releaseName=hej-prod \
  --set secrets.cryptrSecret=copy-test-secret \
  --set auth.mode=v2 \
  --set auth.authority=https://idp.example.invalid/realms/source \
  --set auth.clientId=source-client >"$rendered"

assert_match() {
  local pattern=$1
  local description=$2
  if ! grep -q "$pattern" "$rendered"; then
    echo "FAIL: $description" >&2
    exit 1
  fi
}

assert_no_match() {
  local pattern=$1
  local description=$2
  if grep -q "$pattern" "$rendered"; then
    echo "FAIL: $description" >&2
    exit 1
  fi
}

assert_match 'name: hej-test-mariadb-copy' "clone backup is rendered"
assert_match 'name: hej-prod-mariadb' "clone backup targets the source database"
assert_match 'wait-for-clone' "backend waits for restored data"
assert_match 'backupRef:' "target database bootstraps from the clone backup"
assert_match 'source-client' "SSO client id is retained"
assert_no_match 'name: hej-test-mariadb-init-' "initial seed job is disabled for clones"
assert_no_match 'schedule:' "scheduled test backups are disabled"
assert_no_match 'CLONE_AUTH_' "clone does not rewrite restored SSO config"

if helm template hej-test "$root/charts/hej" \
  --set global.domain=hej-test.example.invalid \
  --set copyFrom.enabled=true \
  --set copyFrom.releaseName=hej-test \
  --set secrets.cryptrSecret=copy-test-secret >/dev/null 2>&1; then
  echo "FAIL: self-replication was accepted" >&2
  exit 1
fi

echo "OK   hej copyFrom renders a backup, restore, and startup gate"
