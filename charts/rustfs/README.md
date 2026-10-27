# rustfs

S3-compatible object storage per organization namespace, as a
[RustFS Operator](https://github.com/rustfs/operator) `Tenant`.

The chart only renders a credentials Secret, a `Tenant` and (optionally) an
Ingress. The operator creates the StatefulSet, PVC and Services.

## Prerequisite

The RustFS Operator must be installed cluster-wide (Tenant CRD
`tenants.rustfs.com`). On gdm-rke2-ai-services it is the ArgoCD app
`apps/rustfs-operator` in gdm-rke2-ai-services-apps.

## What gets created

| Resource | Name | Owner |
|---|---|---|
| Secret (`accesskey`/`secretkey`) | `<fullname>-secrets` | chart |
| Tenant | `<release>` | chart |
| StatefulSet | `<release>-pool-0` | operator |
| PVC | `vol-0-<release>-pool-0-0` | StatefulSet (no owner ref) |
| S3 Service (port 9000) | `<release>-io` | operator |
| Ingress (optional) | `<fullname>` | chart |

The Tenant is named after the release (= the llmportal application name) so
the operator's `app.kubernetes.io/instance` label on pods and PVCs matches the
application. llmportal relies on that label for resource stats and upgrade
verification.

In-cluster S3 endpoint: `http://<release>-io.<namespace>.svc.cluster.local:9000`
(path-style addressing).

Root credentials are generated on first install and reused on upgrade via
`lookup`.

## Lifecycle notes

- **Storage size is fixed at creation.** `volumeClaimTemplates` are immutable,
  and the operator rejects changes to `persistence.size`. To grow storage,
  resize the PVC directly (`fa-rwx` allows expansion).
- **Uninstall keeps the data.** The PVC has no owner reference, so deleting the
  release (and with it the Tenant) leaves the PVC behind. Re-creating with the
  same name re-attaches it. Delete the PVC explicitly to drop the data.
- **Buckets, users and policies** can be declared via `buckets`, `users` and
  `policies`; they are passed through to the Tenant spec unchanged.

## Exposing S3 externally

Ingress is disabled by default; storage is consumed in-cluster (eneo, backups).

```yaml
ingress:
  enabled: true
  host: s3.customer.ai.gdm.se
```
