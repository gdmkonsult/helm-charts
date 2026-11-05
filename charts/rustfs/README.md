# rustfs

S3-compatible object storage per organization namespace, as a
[RustFS Operator](https://github.com/rustfs/operator) `Tenant`.

The chart renders a credentials Secret, a per-instance CA (cert-manager), a
`Tenant` and (optionally) an Ingress. The operator creates the StatefulSet, PVC,
Services and the server certificate.

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
| CA (Issuer, Certificate, Secret) | `<fullname>-selfsigned`, `<fullname>-ca`, `<fullname>-ca-issuer` | chart / cert-manager |
| Server certificate + Secret (`tls.crt`, `tls.key`, `ca.crt`) | `<release>-server-tls` / `<fullname>-server-tls` | operator / cert-manager |
| S3 Service (port 9000, HTTPS) | `<release>-io` | operator |
| Ingress (optional) | `<fullname>` | chart |
| Traefik backend Service + ServersTransport (with Ingress) | `<fullname>-s3` | chart |

The Tenant is named after the release (= the llmportal application name) so
the operator's `app.kubernetes.io/instance` label on pods and PVCs matches the
application. llmportal relies on that label for resource stats and upgrade
verification.

In-cluster S3 endpoint: `https://<release>-io.<namespace>.svc.cluster.local:9000`
(path-style addressing). Clients must trust `ca.crt` from Secret
`<fullname>-server-tls`; plain HTTP is refused.

## In-cluster TLS

`tls.enabled` (default `true`) creates a per-instance CA with cert-manager and
lets the operator request the server certificate from it (SANs: the `-io` and
headless Services and the pod). Certificates are valid `tls.duration` (1 year)
and renewed `tls.renewBefore` (30 days) ahead. Renewal restarts the RustFS pod
(the operator only supports `rotationStrategy: Rollout`), about 30 s for a
single-node instance. The CA (`tls.caDuration`, 10 years) keeps its key on
renewal, so clients keep working with the same `ca.crt`.

Eneo: set `config.objectContentCaSecret: <fullname>-server-tls` in the eneo
chart (mounts only `ca.crt` and sets `OBJECT_CONTENT_CA_BUNDLE`).

Enabling TLS on an existing instance (upgrade from 0.1.x) restarts the pod
once; clients must switch to `https://` and trust the CA.

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
With in-cluster TLS, Traefik terminates the public certificate (Let's Encrypt)
and connects to RustFS over HTTPS, verifying the instance CA via a
`ServersTransport`.

```yaml
ingress:
  enabled: true
  host: s3.customer.ai.gdm.se
```
