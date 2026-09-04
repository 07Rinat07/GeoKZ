# GeoKZ — obtaining and configuring external API keys (EN)

Current as of: 2026-09-04.

## 1. Why GeoKZ may need an API key

GeoKZ can operate fully on its local database without an external API. An API key is required only for external sources that require authenticated programmatic access.

For the official Kazakhstan Open Data portal `data.egov.kz`, the key is used with REST API v4 to synchronize open datasets connected to GeoKZ.

GeoKZ must never store a real API key in Git, README, source code, issues, pull requests, screenshots or user documentation.

## 2. Where to obtain a data.egov.kz key

1. Open the official Kazakhstan Open Data portal: `https://data.egov.kz/`.
2. Sign in using the available eGov authentication method.
3. Open the **Developers / «Разработчикам»** section.
4. Go to the **Developer Cabinet / «Кабинет разработчика»**.
5. Find the API access / API key area and create or copy your personal developer key.
6. Store the key in a password manager or locally in the GeoKZ `.env` file.

The government portal UI may change over time. If the key-management section is moved, use the Developers section, portal help, or official eGov/Open Data support.

## 3. Where to put the key in GeoKZ

Create a local `.env` file from the template at the project root:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set the local value:

```env
GEOKZ_EGOV_API_KEY=YOUR_REAL_KEY
```

Do not add quotes unless the key itself contains them.

Restart the GeoKZ API / Docker Compose after changing `.env` so the settings are reloaded.

## 4. What must never be done with a key

- do not commit `.env` to Git;
- do not paste the key into `README.md`;
- do not hard-code it in Python;
- do not publish it in issues or pull requests;
- do not send it in chat or email unless strictly necessary;
- do not expose it in screenshots;
- if leakage is suspected, revoke/rotate the key in the developer cabinet.

Only the safe empty template belongs in the repository:

```env
GEOKZ_EGOV_API_KEY=
```

## 5. Verify the GeoKZ configuration

After starting the API, open Swagger:

`http://localhost:8000/docs`

Check the official dataset catalog:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

`api_key_configured=true` means GeoKZ sees a non-empty key in its configuration. It does not yet prove that the upstream portal accepts the key.

## 6. Register the official Kazakhstan datasets

In Swagger, execute:

```text
POST /api/v1/integrations/kazakhstan/register
```

GeoKZ registers the known official sources in the external-source registry. Registration does not overwrite verified geological master data.

## 7. First safe synchronization test

For the oil and gas fields dataset:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/sync
```

For geological exploration licenses:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/sync
```

Downloaded records first enter the RAW/staging layer:

```text
data.egov.kz
  → RAW
  → checksum/diff
  → normalization
  → matching
  → review
  → verified GeoKZ master data
```

An external API must never silently overwrite verified GeoKZ values.

## 8. If synchronization fails

Check in this order:

1. `.env` exists;
2. `GEOKZ_EGOV_API_KEY` is set;
3. the application was restarted after changing `.env`;
4. `/api/v1/integrations/kazakhstan/catalog` reports `api_key_configured=true`;
5. `https://data.egov.kz/` is reachable from your network;
6. the key is still valid in the developer cabinet;
7. the portal has not changed the version/schema of the target dataset.

Typical GeoKZ responses:

- HTTP `503` — missing or invalid local API-key/connector configuration;
- HTTP `502` — upstream portal failure or unexpected protocol;
- HTTP `404` — unknown GeoKZ dataset code.

## 9. Current official GeoKZ datasets

At the `v0.2-dev` stage:

- `kz-egov-oil-gas-fields` — oil and gas fields of the Republic of Kazakhstan;
- `kz-egov-geological-study-licenses` — licenses for geological exploration of subsoil.

The registry will expand as additional official open sources are validated.

## 10. Other API keys

Future integrations follow the same rule:

```text
user/organization secret
  → environment/.env or system secret storage
  → Settings
  → Connector
```

API keys must never become part of the geological domain model.
