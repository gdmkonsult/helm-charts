# Multi-tenant Federation — Installationsguide

Den här guiden beskriver hur man konfigurerar Eneo med **per-tenant federation**, så att varje hyresgäst (tenant) kan använda sin egen identitetsleverantör (t.ex. Entra ID) med helt separata subdomäner.

---

## Översikt

| Inställning                  | Utan federation             | Med federation                     |
| ---------------------------- | --------------------------- | ---------------------------------- |
| Autentiseringskälla          | Globala OIDC-miljövariabler | Per-tenant config i databasen      |
| Alla tenants delar samma IdP | Ja                          | Nej — varje tenant har sin egen    |
| Gamla `oidc.*`-värden        | Aktiva                      | Ignoreras (säkert att lämna)       |
| Kräver `ENCRYPTION_KEY`      | Nej                         | Ja (krypterar client secrets i DB) |

---

## Förutsättningar

- Helm-chartet `eneo` installerat
- `cert-manager` installerat i klustret med en fungerande `ClusterIssuer`
- DNS-hantering för att peka subdomänerna till klustrets ingress-IP
- API-åtkomst till Eneo-backenden (SUPER_API_KEY)

---

## Steg 1 — Konfigurera Helm-values

Uppdatera din `values.yaml` (eller override-fil) med följande:

```yaml
config:
  # Aktivera per-tenant federation — OIDC-env-vars ignoreras därefter
  federationPerTenantEnabled: "true"

# Lista alla tenant-subdomäner som behövs
# Varje host läggs till som separat rule + TLS-entry på ingress-objekten.
extraHosts:
  - bengtsfors.eneo.example.com
  - fargelanda.eneo.example.com
  - amal.eneo.example.com
```

> **OBS:** `secrets.encryptionKey` genereras automatiskt om den är tom.  
> Om du redan har en befintlig nyckel, ange den explicit så att befintliga krypterade uppgifter fortsätter fungera.

Uppgradera sedan chartet:

```bash
helm upgrade <release-namn> charts/eneo -f values.yaml -n <namespace>
```

---

## Steg 2 — DNS

Skapa DNS-poster som pekar varje tenant-subdomän till samma ingress-IP:

| Typ       | Namn                          | Mål                  |
| --------- | ----------------------------- | -------------------- |
| CNAME / A | `bengtsfors.eneo.example.com` | Klustrets ingress-IP |
| CNAME / A | `fargelanda.eneo.example.com` | Klustrets ingress-IP |
| CNAME / A | `amal.eneo.example.com`       | Klustrets ingress-IP |

TLS-certifikat hanteras automatiskt av cert-manager (ett cert per host).

---

## Steg 3 — Skapa tenants via API

Alla API-anrop nedan använder headern `X-API-Key` med värdet för `INTRIC_SUPER_API_KEY`.

### 3a. Lista befintliga tenants

```bash
curl -s https://eneo.example.com/api/v1/admin/tenants \
  -H "X-API-Key: <SUPER_API_KEY>" | jq .
```

### 3b. Skapa nya tenants (om de inte finns)

```bash
curl -X POST https://eneo.example.com/api/v1/admin/tenants \
  -H "X-API-Key: <SUPER_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Bengtsfors"}'
```

Upprepa för varje kommun. Notera det returnerade `tenant_id` (UUID).

### 3c. Backfill slugs

```bash
curl -X POST https://eneo.example.com/api/v1/admin/tenants/backfill-slugs \
  -H "X-API-Key: <SUPER_API_KEY>"
```

---

## Steg 4 — Konfigurera federation per tenant

Ersätt `{TENANT_UUID}` med det faktiska UUID:t från steg 3.

```bash
curl -X PUT https://eneo.example.com/api/v1/admin/tenants/{TENANT_UUID}/federation \
  -H "X-API-Key: <SUPER_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "oidc_discovery_url": "https://login.microsoftonline.com/<ENTRA_TENANT_ID>/v2.0/.well-known/openid-configuration",
    "client_id": "<APP_REGISTRATION_CLIENT_ID>",
    "client_secret": "<APP_REGISTRATION_CLIENT_SECRET>",
    "allowed_domains": ["kommun.bengtsfors.se"],
    "canonical_public_origin": "https://bengtsfors.eneo.example.com"
  }'
```

> **Viktigt:** `canonical_public_origin` måste matcha **exakt** vad som registreras som redirect URI i Entra ID.

Upprepa för varje tenant med korrekta värden.

---

## Steg 5 — Registrera redirect URI i Entra ID

I varje Entra ID App Registration, lägg till redirect URI:

| Tenant     | Redirect URI                                        |
| ---------- | --------------------------------------------------- |
| Bengtsfors | `https://bengtsfors.eneo.example.com/auth/callback` |
| Färgelanda | `https://fargelanda.eneo.example.com/auth/callback` |
| Åmål       | `https://amal.eneo.example.com/auth/callback`       |

---

## Steg 6 — Verifiera

Testa varje tenant genom att öppna subdomänen i webbläsaren:

```
https://bengtsfors.eneo.example.com
https://fargelanda.eneo.example.com
https://amal.eneo.example.com
```

Respektive tenant ska omdirigera till sin egen Entra ID-inloggning.

---

## Viktiga detaljer

- **`allowed_domains`** styr vilka e-postadresser som kan logga in — anpassa om kommunerna har egna domäner
- **`canonical_public_origin`** bestämmer redirect URI, måste matcha exakt med det som registreras i Azure
- Användare behöver fortfarande skapas/bjudas in per tenant — federation hanterar enbart autentisering
- Om du byter tillbaka till `federationPerTenantEnabled: "false"` används de globala `oidc.*`-värdena igen — federation-konfigurationen i databasen ignoreras

---

## Felsökning

| Problem                            | Orsak                                                            | Lösning                                             |
| ---------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------- |
| 404 på tenant-subdomän             | DNS pekar inte rätt, eller host saknas i `extraHosts`            | Kontrollera DNS och `values.yaml`                   |
| TLS-fel                            | cert-manager har inte utfärdat cert                              | `kubectl get certificates -n <ns>` och kolla events |
| OIDC redirect-fel                  | `canonical_public_origin` matchar inte redirect URI i Azure      | Kontrollera att URL:erna är identiska               |
| Validerings-fel vid `helm upgrade` | `extraHosts` satt men `federationPerTenantEnabled` inte `"true"` | Sätt `config.federationPerTenantEnabled: "true"`    |
