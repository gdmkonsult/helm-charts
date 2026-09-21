{{/*
Expand the name of the chart.
*/}}
{{- define "switchyard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "switchyard.fullname" -}}
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
{{- define "switchyard.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "switchyard.labels" -}}
helm.sh/chart: {{ include "switchyard.chart" . }}
{{ include "switchyard.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "switchyard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "switchyard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate or retrieve router API key
*/}}
{{- define "switchyard.apiKey" -}}
{{- $secretName := printf "%s-secret" (include "switchyard.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if and $secret (hasKey $secret.data "ROUTER_API_KEY") -}}
{{- index $secret.data "ROUTER_API_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{- randAlphaNum 32 | printf "csk_%s" -}}
{{- end -}}
{{- end }}
