# Rules for agents and humans editing these charts

These charts run production databases for many customers. On 2026-10-08 a chart change
(eneo 1.0.183–1.0.186) deleted 14 production Postgres clusters on upgrade. Follow these
rules without exception; CI enforces most of them and blocks publishing if they fail.

## Never
- **Never add `helm.sh/hook` to anything except a Job or Pod.** Helm deletes and recreates
  hook resources and drops them from the release; on upgrade that deletes the existing
  object (CNPG Cluster → PVCs → data). Not for ConfigMaps, Secrets, Clusters, ObjectStores,
  ScheduledBackups, PVCs — not "just to fix install ordering".
- **Never remove, rename, or put behind a new default-off flag** an existing Cluster, PVC,
  Secret, ObjectStore or ScheduledBackup. Anything that leaves the rendered manifest is
  deleted by Helm on the next upgrade.
- **Never remove `helm.sh/resource-policy: keep`** from a CNPG `Cluster`.
- Never make a pre-install hook depend on a non-hook resource (it doesn't exist yet on fresh
  install). Fix ordering in the app (init containers / retries) instead.

## Always
- Run before committing: `./scripts/check-hook-deps.sh && ./scripts/check-upgrade-safety.sh`
- Bump `version` in `Chart.yaml` for every chart change.
- Test upgrades from the *previous released version* on a test namespace before rollout,
  and verify the Postgres `Cluster` keeps the same `metadata.uid`.
- Never `helm upgrade --reuse-values` (it resurrects old chart defaults); pass the
  HelmChart `spec.valuesContent` with `-f` like the helm-controller does.
