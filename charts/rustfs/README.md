# rustfs

Single-node RustFS S3-compatible object storage, deployed per organization
namespace. One Deployment + one RWO PVC; no distributed/erasure-coded mode.

## Usage

```bash
helm template charts/rustfs --set global.domain=example.com
```

Credentials are auto-generated on first install and persisted in
`<fullname>-secrets` (keys `RUSTFS_ACCESS_KEY` / `RUSTFS_SECRET_KEY`).
Subsequent upgrades reuse the existing secret via `lookup`.

## Exposing S3 externally

Ingress is **disabled by default** — storage is consumed in-cluster
(eneo, CNPG/Velero backups). For customers buying standalone S3 buckets:

```yaml
ingress:
  enabled: true
  host: s3.customer.ai.gdm.se
```

S3 clients must use path-style addressing (`https://s3.customer.ai.gdm.se/bucket/key`),
not virtual-hosted style.

## Notes

- Container runs as non-root uid 10001 (`rustfs` user in the image).
- PVC default: `px-fa-direct-access`, 50Gi.
- Console (port 9001) is off by default and never exposed via ingress.
