{{/*
Expand the name of the chart.
*/}}
{{- define "n8n.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "n8n.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "n8n.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "n8n.labels" -}}
helm.sh/chart: {{ include "n8n.chart" . }}
{{ include "n8n.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "n8n.selectorLabels" -}}
app.kubernetes.io/name: {{ include "n8n.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate encryption key if not set, but preserve existing value on upgrade
*/}}
{{- define "n8n.generateEncryptionKey" -}}
{{- $secretName := printf "%s-secrets" (include "n8n.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "N8N_ENCRYPTION_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Generate runner token if not set, but preserve existing value on upgrade
*/}}
{{- define "n8n.generateRunnerToken" -}}
{{- $secretName := printf "%s-secrets" (include "n8n.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "N8N_RUNNERS_AUTH_TOKEN" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Validate required values
*/}}
{{- define "n8n.validateValues" -}}
{{- if not .Values.global.domain -}}
{{- fail "global.domain is required. Please set it in your values.yaml or via --set global.domain=your-domain.com" -}}
{{- end -}}
{{- end -}}

{{/*
Resolve image repository and tag per component, falling back to shared image.*
*/}}
{{- define "n8n.mainImage" -}}
{{- $repo := default .Values.image.repository .Values.main.image.repository -}}
{{- $tag := default .Values.image.tag .Values.main.image.tag -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}

{{- define "n8n.runnerImage" -}}
{{- $repo := default "n8nio/runners" .Values.runner.image.repository -}}
{{- $tag := default .Values.image.tag .Values.runner.image.tag -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}

{{- define "n8n.workerImage" -}}
{{- $repo := default .Values.image.repository .Values.worker.image.repository -}}
{{- $tag := default .Values.image.tag .Values.worker.image.tag -}}
{{- printf "%s:%s" $repo $tag -}}
{{- end -}}

{{/*
Size profiles: standard, premium, premium-plus
Each profile defines defaults for resources, scaling, and config.
Explicit values in values.yaml always override profile defaults.
*/}}
{{- define "n8n.profiles" -}}
standard:
  config:
    executionsMode: "regular"
    dbPoolSize: "10"
  main:
    replicaCount: 1
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 512Mi
  runner:
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 256Mi
  worker:
    replicaCount: 0
    resources:
      limits:
        cpu: "2"
        memory: 2Gi
      requests:
        cpu: "100m"
        memory: 512Mi
  postgres:
    instances: 1
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 1Gi
    postgresql:
      shared_buffers: "1GB"
      effective_cache_size: "3GB"
      work_mem: "8MB"
      maintenance_work_mem: "256MB"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      max_connections: "100"
  redis:
    resources:
      limits:
        cpu: "1"
        memory: 1Gi
      requests:
        cpu: "100m"
        memory: 128Mi
premium:
  config:
    executionsMode: "queue"
    dbPoolSize: "20"
  main:
    replicaCount: 1
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 512Mi
  runner:
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 256Mi
  worker:
    replicaCount: 2
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 512Mi
  postgres:
    instances: 1
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 1Gi
    postgresql:
      shared_buffers: "1GB"
      effective_cache_size: "3GB"
      work_mem: "8MB"
      maintenance_work_mem: "256MB"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      max_connections: "100"
  redis:
    resources:
      limits:
        cpu: "2"
        memory: 2Gi
      requests:
        cpu: "100m"
        memory: 128Mi
premium-plus:
  config:
    executionsMode: "queue"
    dbPoolSize: "50"
  main:
    replicaCount: 1
    resources:
      limits:
        cpu: "8"
        memory: 8Gi
      requests:
        cpu: "200m"
        memory: 1Gi
  runner:
    resources:
      limits:
        cpu: "8"
        memory: 8Gi
      requests:
        cpu: "200m"
        memory: 512Mi
  worker:
    replicaCount: 4
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 512Mi
  postgres:
    instances: 1
    resources:
      limits:
        cpu: "4"
        memory: 4Gi
      requests:
        cpu: "100m"
        memory: 1Gi
    postgresql:
      shared_buffers: "1GB"
      effective_cache_size: "3GB"
      work_mem: "8MB"
      maintenance_work_mem: "256MB"
      random_page_cost: "1.1"
      effective_io_concurrency: "200"
      max_connections: "100"
  redis:
    resources:
      limits:
        cpu: "2"
        memory: 2Gi
      requests:
        cpu: "200m"
        memory: 256Mi
{{- end -}}

{{/*
Get the active size profile
*/}}
{{- define "n8n.profile" -}}
{{- $profiles := include "n8n.profiles" . | fromYaml -}}
{{- $size := .Values.size | default "standard" -}}
{{- if not (hasKey $profiles $size) -}}
{{- fail (printf "Invalid size '%s'. Must be one of: standard, premium, premium-plus" $size) -}}
{{- end -}}
{{- index $profiles $size | toYaml -}}
{{- end -}}

{{/*
Resolve a value: use explicit override if set, otherwise fall back to profile default.
Usage: include "n8n.resolve" (dict "override" .Values.x.y "profile" $profile.x.y)
*/}}
{{- define "n8n.resolveResources" -}}
{{- if .override -}}
{{- toYaml .override -}}
{{- else -}}
{{- toYaml .profile -}}
{{- end -}}
{{- end -}}
