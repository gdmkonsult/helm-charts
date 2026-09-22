# Switchyard Helm Chart

En produktionsklar, högtillgänglig Helm-chart för [NVIDIA NeMo Switchyard](https://github.com/NVIDIA-NeMo/Switchyard) – en asynkron och resurssnål modellrouter byggd i Rust.

## Översikt & Arkitektur

Switchyard placeras mellan AI-klienter (t.ex. *Hej*, *Cursor*, *Claude Code*, egna Python-skript) och modellernas API-endpoints (Azure OpenAI, Azure AI Foundry, Anthropic, GDM AI, m.fl.).

```
                                KLIENTAPPLIKATION
                     (Hej, Cursor, Claude Code, Python SDK)
                                      │
                                      │ Bearer <ROUTER_API_KEY>
                                      ▼
                        ┌───────────────────────────┐
                        │    TRAEFIK INGRESS (TLS)  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │   AUTH-PROXY (Nginx Pod)  │
                        │  Validerar API-nyckel     │
                        └─────────────┬─────────────┘
                                      │ (Lokal HTTP :4000)
                                      ▼
                        ┌───────────────────────────┐
                        │      SWITCHYARD (Rust)    │
                        │  Smart modellroutning     │
                        └───────┬───────────┬───────┘
                                │           │
                ┌───────────────┘           └───────────────┐
                ▼                                           ▼
       [ Snabb modell ]                            [ Kraftfull modell ]
     (t.ex. Phi-4 / Luna)                        (t.ex. GPT-4o / Terra)
```

### Huvudegenskaper

1. **Dynamisk modellista (1 till oändligt många modeller):**
   - **1 modell:** Körs automatiskt som **Passthrough** direkt till modellen (med fördelarna av TLS, API-nyckelskydd och Prometheus-metrik).
   - **2 modeller:** Körs automatiskt som **Stage Router** (Snabb basmodell $\leftrightarrow$ Kraftfull eskalering).
   - **3+ modeller:** Multi-Tier arkitektur (t.ex. *Luna* $\to$ *Sol* $\to$ *Terra*). Huvudrouten (`switchyard`) balanserar automatiskt, samtidigt som varje modell även exponeras som en direkt anropsbar rutt med sitt eget modellnamn.
2. **Ingen `api-version` krävs:**
   - För Azure OpenAI läggs stabil `api-version=2024-10-21` till automatiskt om det saknas i bas-URL:en.
3. **Automatisk protokollöversättning:**
   - OpenAI Chat Completions (`/v1/chat/completions`) $\leftrightarrow$ Anthropic Messages (`/v1/messages`).
   - Claude Code kan anropa Azure OpenAI-modeller, och OpenAI-klienter kan anropa Anthropic Claude.
4. **Felåterhämtning & Fallback:**
   - Automatisk omprövning (`max_retries`) vid transportfel, HTTP 408 (timeout), 429 (rate limit) och 5xx.
   - Vid kvarstående fel växlar Switchyard automatiskt till nästa kandidatmodell i kedjan.
5. **Hög tillgänglighet (HA):**
   - 2 repliker som standard med `podAntiAffinity` som sprider poddarna över olika noder.

---

## Konfiguration (`values.yaml`)

### Exempel med 3 modeller (Multi-Tier)

```yaml
replicaCount: 2

auth:
  enabled: true
  apiKey: "csk_live_hejkund_2026"

models:
  - id: "gpt-5.6-luna"
    provider: "azure_foundry"
    baseUrl: "https://kund-luna.swedencentral.models.ai.azure.com/v1"
    apiKey: "kundens-luna-nyckel"

  - id: "gpt-5.6-sol"
    provider: "azure_openai"
    baseUrl: "https://kund.openai.azure.com"
    apiKey: "kundens-azure-nyckel"

  - id: "gpt-5.6-terra"
    provider: "azure_openai"
    baseUrl: "https://kund.openai.azure.com"
    apiKey: "kundens-azure-nyckel"

router:
  routeId: "switchyard"
  picker: "efficient_first"
  confidenceThreshold: 0.5
```

---

## Hur klienter ansluter

### 1. Hej (Backend `.env`)
```env
OPENAI_BASE_URL=https://<app-namn>.<org-namn>.ai.gdm.se/v1
OPENAI_API_KEY=csk_live_hejkund_2026
MODEL=switchyard
```

### 2. cURL (OpenAI Chat API)
```bash
curl https://<app-namn>.<org-namn>.ai.gdm.se/v1/chat/completions \
  -H "Authorization: Bearer csk_live_hejkund_2026" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "switchyard",
    "messages": [{"role": "user", "content": "Hej!"}]
  }'
```

### 3. Claude Code / Anthropic API
```bash
export ANTHROPIC_BASE_URL="https://<app-namn>.<org-namn>.ai.gdm.se"
export ANTHROPIC_API_KEY="csk_live_hejkund_2026"
export ANTHROPIC_MODEL="switchyard"
claude
```
