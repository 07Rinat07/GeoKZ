# GeoKZ — v0.3+ өзекті даму жоспары

Күйі: `2026-09-05`, ағымдағы feature: `feature/geological-study-license-review-v0.3`.

## Мақсат
GeoKZ Қазақстан геологиясы үшін evidence-based бірыңғай жұмыс ортасы болуы тиіс: аумақ/координата → жақын кен орындары, құрылымдар, ұңғымалар, сейсмика → паспорттар → lithology, reservoir, logs, core, tests, oil/gas/water → көрші ұңғымаларды correlation → source/provenance/conflict/review.

Пайдаланушы өнімі және documentation RU/KK/EN жүргізіледі. External API GeoKZ-ті байытады, бірақ verified master data-ны автоматты түрде қайта жазбайды және offline-capable core-ды алмастырмайды.

## Main ішінде іске асқан мүмкіндіктер

- FastAPI + PostgreSQL/PostGIS + async SQLAlchemy + Alembic;
- real PostgreSQL/PostGIS CI және migration-to-head gate;
- territory explorer, Geological Entity Passport, Well Passport;
- geographic/projected X/Y, dot/comma, WGS84/UTM helper;
- confirmed persistent organization-local CRS registry EPSG/WKT/PROJ;
- nearby PostGIS search;
- trajectory, logs, tests, core, 2D/3D seismic subsurface models;
- WellMarker және TVDSS/TVD/MD depth-safe correlation;
- visual cross-section: `POST /api/v1/correlation/wells/view`;
- synthetic demo: `POST /api/v1/correlation/demo/workflow`;
- Kazakhstan Open Data connector, metadata/mapping/schema inspection;
- Update All: `POST /api/v1/integrations/sync-all`;
- scheduler status: `GET /api/v1/integrations/scheduler/status`;
- run due: `POST /api/v1/integrations/scheduler/run-due`;
- oil/gas field processing: `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`;
- field review: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`;
- localized field-review view: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`;
- controlled vocabulary registry (`lithology`, `marker_type`, `property_kind`, `unit`) және subsurface canonical bindings, RAW/source wording сақталады;
- correlation distance query cartesian-product warning жойылды және PostGIS regression test қосылды.

## Ағымдағы P0 — геологиялық зерттеу лицензиялары

```text
GeoKZ code:  kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

Feature branch ішінде:

- әкімшілік license normalizer;
- өзгермейтін `raw_payload`;
- `license_number`, `issue_date`, type/scope, term, basis, authority, holder, BIN;
- Alembic `20260905_0008`: `reviewed_by`, `reviewed_at`, `review_comment`;
- record-level `REVIEW_REQUIRED → ACCEPTED/REJECTED`;
- автоматты `ExternalEntityLink` жоқ, өйткені тексерілген v6 карточкасы stable geological-object/geometry identifier бермейді;
- upstream `CHANGED` бұрынғы reviewer шешімін invalid етеді;
- unit және PostgreSQL/PostGIS HTTP integration tests;
- RU/KK/EN жеке guide.

API:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

Merge gate: final exact-head Python quality + PostgreSQL/PostGIS integration жасыл болуы керек, содан кейін сол head үшін PR-CI жасыл болса ғана squash merge `main`.

## Келесі P0

### 1. GeoKZ Core Dataset manifest/importer

- versioned `manifest.json`;
- dataset/schema version, created_at, SHA-256;
- transactional import және rollback;
- entities/sources/facts/regions/vocabularies baseline;
- About/Data Sources ішінде Core Dataset version;
- checksum validation және кейін digital signature;
- repeated import, incompatible schema және rollback tests.

### 2. Authentication + AuditLog/Revision

- expert/editor/admin roles;
- review және master-data өзгерістері үшін audit trail;
- Fact/Entity/geometry/interpretation revision history;
- verified data silent overwrite жасалмайды;
- controlled vocabulary write API тек roles/audit дайын болғаннан кейін.

### 3. Production PySide6 screens

- Data Sources + «Update All»;
- scheduler due/running/error/version;
- server-owned actions арқылы field review;
- license ACCEPT/REJECT queue;
- provenance panel және RU/KK/EN contextual help.

### 4. Kazakhstan ресми геологиялық datasets кеңейту

Әрбір жаңа source current metadata/mapping/license/terms арқылы тексеріледі. Бірдей provider SDK, RAW + checksum/diff + typed normalizer + review rules + contract tests қолданылады; әр dataset үшін қажетсіз duplicated business logic жасалмайды.

### 5. Global context

Кейін USGS, Macrostrat, OneGeology/OGC және Copernicus observation assets. Source/version/retrieved_at/license/attribution міндетті сақталады.

## Definition of Done

```text
feature
→ code/migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated RU/KK/EN docs
→ exact-head CI green
→ PR
→ PR-CI green
→ squash merge main
→ келесі roadmap item
```

Негізгі қағида: GeoKZ external services жоқ кезде де жұмыс істейді; internet тек evidence-based local database-ті қауіпсіз толықтырады.
