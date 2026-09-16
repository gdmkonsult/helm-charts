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

### Flow preview

Set `appVersion` to the Flow preview branch or image tag, for example:

```yaml
appVersion: "refactor-flows-tidy-ai-builder"
```

Enable both Flow execution processes in the release values:

```yaml
celeryWorker:
	enabled: true
celeryBeat:
	enabled: true
```

Both are required: `celery-worker` executes the `flows.execute` queue and
`celery-beat` reconciles stale runs, redispatches, review checkpoints, and
audit/webhook outbox work. Without them, Flow runs can remain queued or fail to
self-heal after an interruption.

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
