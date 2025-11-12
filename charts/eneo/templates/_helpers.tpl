{{/*
Expand the name of the chart.
*/}}
{{- define "eneo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "eneo.fullname" -}}
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
{{- define "eneo.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "eneo.labels" -}}
helm.sh/chart: {{ include "eneo.chart" . }}
{{ include "eneo.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "eneo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "eneo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Generate a random secret if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateSecret" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .) -}}
{{- $secret := lookup "v1" "Secret" .Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "JWT_SECRET" | b64dec -}}
{{- else if . -}}
{{ . }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Generate JWT secret if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateJwtSecret" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "JWT_SECRET" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Generate URL signing key if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateUrlSigningKey" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "URL_SIGNING_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Generate encryption key if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateEncryptionKey" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "ENCRYPTION_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 32 | b64enc }}
{{- end -}}
{{- end -}}

{{/*
Generate INTRIC_SUPER_API_KEY if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateIntricSuperApiKey" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "INTRIC_SUPER_API_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 32 }}
{{- end -}}
{{- end -}}

{{/*
Generate INTRIC_SUPER_DUPER_API_KEY if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateIntricSuperDuperApiKey" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "INTRIC_SUPER_DUPER_API_KEY" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{ randAlphaNum 64 }}
{{- end -}}
{{- end -}}

{{/*
Generate DEFAULT_USER_PASSWORD if not set, but preserve existing value on upgrade
*/}}
{{- define "eneo.generateDefaultUserPassword" -}}
{{- $secretName := printf "%s-secrets" (include "eneo.fullname" .context) -}}
{{- $secret := lookup "v1" "Secret" .context.Release.Namespace $secretName -}}
{{- if $secret -}}
{{- index $secret.data "DEFAULT_USER_PASSWORD" | b64dec -}}
{{- else if .value -}}
{{ .value }}
{{- else -}}
{{- $cached := .context.Release.Name | sha256sum | trunc 16 -}}
{{ $cached }}
{{- end -}}
{{- end -}}

{{/*
Validate required values
*/}}
{{- define "eneo.validateValues" -}}
{{- if not .Values.global.domain -}}
{{- fail "global.domain is required. Please set it in your values.yaml or via --set global.domain=your-domain.com" -}}
{{- end -}}
{{- end -}}
