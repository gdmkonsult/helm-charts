## Switching between stable and Flow images

The image tag for the Eneo backend, frontend, ARQ worker, Celery worker, and
Celery beat is controlled by `appVersion` in `Chart.yaml`. It is deliberately
not derived from the Helm release name or pod name.

### Stable release

Set `appVersion` to the released Eneo version, for example:

```yaml
appVersion: "2.1.1"
```

Keep the Flow-only processes disabled unless the selected image explicitly
supports them:

```yaml
celeryWorker:
	enabled: false
celeryBeat:
	enabled: false
```

### Upgrading to Eneo 2.2

The chart emits both the legacy `INTRIC_BACKEND_*` frontend variables and the
new `ENEO_BACKEND_*` names so 2.1 and 2.2 images remain supported during the
transition. It also emits both `FEDERATION_PER_TENANT_ENABLED` and its
replacement, `FEDERATION_ENABLED`.

Eneo 2.2 introduces a guarded migration for legacy File/Icon content. Existing
content remains readable while the worker reports `waiting_for_capacity`. Check
the worker log for the required cumulative bytes, reserve sufficient PostgreSQL
payload, WAL, and safety headroom, then set the acknowledgement in release
values to at least the reported number:

```yaml
config:
  fileIconBackfillInlineCapacityAck: "<required-bytes>"
```

Do not raise this value without confirming storage capacity. The default `0`
intentionally leaves the migration paused. Eneo 2.2 continues to use the ARQ
worker entrypoint and does not recognize the Flow-only Celery switches, so keep
`celeryWorker.enabled` and `celeryBeat.enabled` disabled for this release.

### Flow preview

Set `appVersion` to a commit-pinned Flow image tag (`<branch>-<sha7>`), for
example:

```yaml
appVersion: "feature-flows-and-builder-b798729"
```

Do not use the bare branch tag (e.g. `refactor-flows-tidy-ai-builder`): it is
rebuilt on every push, so nodes that pull it later (rescheduling, node loss)
silently get a different build than the rest of the release. The
`feature/flows-and-builder` branch carries Flows on top of develop (2.2+).

Enable both Flow execution processes in the release values:

```yaml
celeryWorker:
	enabled: true
celeryBeat:
	enabled: true
```

Both are required: `celery-worker` runs the image's `task-execution-worker`
(`flows.execute`) and `celery-beat` runs `task-maintenance-worker`, which
reconciles stale runs, redispatches, review checkpoints, and audit/webhook
outbox work. Without them, Flow runs can remain queued or fail to self-heal
after an interruption. Despite the names they are ARQ processes; the chart sets
their `command`, since `run.sh` ignores `RUN_AS_CELERY_*`.

Flow images built from develop refuse to start while retired settings differ
from their old default. Set this in the release values of Flow releases:

```yaml
config:
  tenantWorkerSemaphoreTtlSeconds: "39600"
```

### Apply a switch

Change `Chart.yaml` and the release values, then validate and upgrade the same
Helm release:

```bash
helm lint charts/eneo

helm template <release> charts/eneo \
	--namespace <namespace> \
	--set-string global.domain=<domain> \
	-f <release-values.yaml>

helm upgrade <release> charts/eneo \
	--namespace <namespace> \
	-f <release-values.yaml> \
	--wait
```

Use `helm upgrade --install` instead of `helm upgrade` when the release may not
exist yet. The namespace, domain, and release name must remain the same when
switching an existing installation so that the existing database and generated
secrets are reused.

The chart runs database migrations as a pre-install/pre-upgrade hook before the
application workloads are rolled out. Review the rendered image tags and the
Celery resources before applying a switch:

```bash
helm template <release> charts/eneo \
	--namespace <namespace> \
	--set-string global.domain=<domain> \
	-f <release-values.yaml> \
	| grep -E 'image:|name: eneo-(celery-worker|celery-beat)|RUN_AS_CELERY'
```

### Roll back

Use Helm history to identify the previous revision and roll back the release:

```bash
helm history <release> --namespace <namespace>
helm rollback <release> <revision> --namespace <namespace> --wait
```

Do not switch only the frontend or only the backend image. All application
images come from `Chart.yaml.appVersion` and must stay on the same channel.

## Tool runtime (Eneo 2.3.0 and later)

Only chart 1.0.202 and later (Eneo 2.3.0+) contain the runtime; older charts
ignore `toolRuntime.enabled`. llmportal refuses to enable it on such releases.

`toolRuntime.enabled: true` deploys `ghcr.io/eneo-ai/eneo-tool-runtime` (same
`appVersion` as the backend), which serves the **Ask a file**, **Create a
file**, **Charts** and **Compute** Functions. Off by default; not available on
Flow `appVersion`s.

Enabling it adds `TOOL_RUNTIME_URL` and `FILE_REFERENCE_BASE_URL` to the
configmap and a generated `TOOL_RUNTIME_TOKEN` to the secret, so backend and
worker roll automatically. It also adds a NetworkPolicy: only this release may
call the runtime, and the runtime may only reach this release's backend and DNS.

- Resources: limit 2 CPU / 2 GiB, request 50m / 128 Mi, matching upstream's
  reference stack. `/tmp` is a 512 Mi memory-backed `emptyDir` counted in that
  limit. Concurrency uses upstream defaults; override in `toolRuntime.env` and
  raise the memory limit with it.
- Scheduled only on nodes with kernel > 6 (NFD label), where Landlock confines
  both files and TCP. `TOOL_RUNTIME_REQUIRE_CONFINEMENT=true` makes the pod
  refuse to start otherwise.
- Verify: the start-up log line shows `"confinement":{"files":true,"tcp":true}`,
  and **Admin > Tools** in Eneo shows the runtime as connected.
- `FILE_REFERENCE_BASE_URL` becomes the in-cluster backend address, which also
  applies to signed file links handed to external MCP servers.

Then turn the Functions on in Eneo under **Admin > Tools > Functions**.
