# n8n Helm Chart

A Helm chart for deploying [n8n](https://n8n.io/) workflow automation on Kubernetes.

## Components

- **n8n main** — The main n8n server instance
- **n8n runner** — External task runner for code execution
- **PostgreSQL** — Database backend (via CloudNativePG operator)

## Prerequisites

- Kubernetes 1.24+
- Helm 3.x
- [CloudNativePG operator](https://cloudnative-pg.io/) installed (for PostgreSQL)
- cert-manager (for TLS)
- Traefik ingress controller (or change `ingress.className`)

## Installation

```bash
helm install n8n ./charts/n8n \
  --namespace n8n \
  --create-namespace \
  --set global.domain=n8n.example.com
```

## Configuration

| Parameter | Description | Default |
|---|---|---|
| `global.domain` | Domain name for n8n (required) | `""` |
| `main.enabled` | Enable main n8n instance | `true` |
| `main.replicaCount` | Number of main replicas | `1` |
| `main.image.repository` | Main image repository | `ghcr.io/gdmkonsult/n8n` |
| `main.image.tag` | Main image tag | `v1.123.6` |
| `main.service.port` | Main service port | `5678` |
| `main.persistence.enabled` | Enable data persistence | `true` |
| `main.persistence.size` | PVC size | `10Gi` |
| `runner.enabled` | Enable task runner | `true` |
| `runner.replicaCount` | Number of runner replicas | `1` |
| `runner.image.repository` | Runner image repository | `n8nio/runners` |
| `runner.image.tag` | Runner image tag | `1.123.6` |
| `postgres.enabled` | Enable PostgreSQL | `true` |
| `postgres.instances` | Number of PostgreSQL instances | `1` |
| `postgres.database` | Database name | `n8n` |
| `postgres.storage.size` | PostgreSQL storage size | `20Gi` |
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `traefik` |
| `ingress.tls.enabled` | Enable TLS | `true` |
| `config.timezone` | Timezone | `Europe/Stockholm` |
| `config.runners.enabled` | Enable external runners | `true` |
| `secrets.encryptionKey` | n8n encryption key (auto-generated) | `""` |
| `secrets.runnerToken` | Runner auth token (auto-generated) | `""` |
| `inferens.enabled` | Auto-provision GDM inference credential in n8n | `false` |
| `inferens.apiKey` | API key used for GDM inference credential | `""` |
| `inferens.endpoint` | OpenAI-compatible inference base URL | `""` |
| `inferens.credentialName` | Credential name created in n8n | `"GDM Inference"` |
| `inferens.defaultModel` | Optional default model hint in credential | `""` |
| `mcp.enabled` | MCP feature toggle value (set by llmportal n8n form) | `false` |

## Secrets

The chart auto-generates `encryptionKey` and `runnerToken` on first install and preserves them across upgrades. You can also set them explicitly in your values file.

When `inferens.enabled=true`, you must also set:

- `secrets.adminEmail`
- `secrets.adminPassword`
- `inferens.apiKey`

The chart then runs a bootstrap sidecar that logs into n8n and creates/updates an OpenAI-compatible credential pointing at the configured inference endpoint.

If you use llmportal's n8n application form, `mcp.enabled` is also written from the MCP switch. Keep `mcp.enabled` disabled unless inference/GDM models are enabled for the organization.

## Upgrading

```bash
helm upgrade n8n ./charts/n8n --namespace n8n
```
