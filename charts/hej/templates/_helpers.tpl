{{/*
Expand the name of the chart.
*/}}
{{- define "hej.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "hej.fullname" -}}
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
Compute the fullname of the source release for copyFrom cloning.
*/}}
{{- define "hej.sourceFullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Values.copyFrom.releaseName }}
{{- .Values.copyFrom.releaseName | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Values.copyFrom.releaseName $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Validate values that cannot be left ambiguous during cloning.
*/}}
{{- define "hej.validateValues" -}}
{{- if .Values.copyFrom.enabled }}
{{- if not .Values.copyFrom.releaseName }}
{{- fail "copyFrom.releaseName is required when copyFrom.enabled is true" }}
{{- end }}
{{- if eq .Values.copyFrom.releaseName .Release.Name }}
{{- fail "copyFrom.releaseName must reference another Hej release" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "hej.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "hej.labels" -}}
helm.sh/chart: {{ include "hej.chart" . }}
{{ include "hej.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "hej.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hej.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
MariaDB host name inside namespace
*/}}
{{- define "hej.mariadbHost" -}}
{{- printf "%s-mariadb" (include "hej.fullname" .) }}
{{- end }}

{{/*
Backend host name inside namespace
*/}}
{{- define "hej.backendHost" -}}
{{- printf "%s-backend" (include "hej.fullname" .) }}
{{- end }}

{{/*
Tool runtime (GDM Runtime Tools) host name inside namespace
*/}}
{{- define "hej.toolRuntimeHost" -}}
{{- printf "%s-tool-runtime" (include "hej.fullname" .) }}
{{- end }}

{{/*
The backend port that serves only GET /api/internal/runtime-files/<token>.
The tool runtime may reach this port and nothing else on the backend.
*/}}
{{- define "hej.backendRuntimeFilesPort" -}}8081{{- end }}

{{- define "hej.backendRuntimeFilesOrigin" -}}
{{- printf "http://%s:%s" (include "hej.backendHost" .) (include "hej.backendRuntimeFilesPort" .) }}
{{- end }}

{{/*
Headless Service that only resolves to ready backend pods of the current pod
spec. The frontend waits on it, so a previous backend that is still running
during an upgrade can't satisfy the wait.
*/}}
{{- define "hej.backendCurrentHost" -}}
{{- printf "%s-backend-current" (include "hej.fullname" .) }}
{{- end }}

{{/*
Hash of the backend pod spec (no secret values, only secretKeyRefs).
*/}}
{{- define "hej.backendRolloutToken" -}}
{{- include "hej.backendPodSpec" . | sha256sum | trunc 16 }}
{{- end }}
