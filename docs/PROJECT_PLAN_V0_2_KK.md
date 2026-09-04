# GeoKZ — v0.2+ өзекті даму жоспары

Мәртебе: `2026-09-04`, тармақ `feature/local-crs-registry-v0.3`.

## Мақсаты
GeoKZ — Қазақстан геологиясына арналған дәлелге негізделген жүйе: аумақ/координата → объект → ұңғыма → интервалдар/ҰГЗ/керн/сынақ → корреляция → дереккөз және дәлел.

## Міндетті қағидалар
- RU/KK/EN барлық user-facing функциялар мен documentation ішінде.
- Verified master data сыртқы API немесе AI арқылы review-сіз өзгермейді.
- RAW және бастапқы құжаттар interpretation-нан бөлек сақталады.
- CRS, axis order, MD/TVD/TVDSS және units әрқашан explicit.
- Core Dataset интернетсіз жұмыс істейді.
- Synthetic/demo data production data-дан бөлек.
- UI backend business rules логикасын қайталамайды.
- Periodic external sync dedicated process/service арқылы орындалады.

## Іске асырылды
- ✅ FastAPI + PostgreSQL/PostGIS + SQLAlchemy async + Alembic.
- ✅ PostgreSQL/PostGIS CI, migrations, PostGIS, pg_trgm және unaccent.
- ✅ Territory Explorer, Geological Entity Passport және Well Passport.
- ✅ geographic/projected coordinate input, WGS84/UTM helper және pyproj/PROJ resolution.
- ✅ `POST /api/v1/spatial/nearby` және нақты PostGIS integration test.
- ✅ trajectory, well logs, tests, core, seismic және Well Correlation.
- ✅ `POST /api/v1/correlation/wells` және backend-owned `POST /api/v1/correlation/wells/view`.
- ✅ safe visual cross-section: `TVDSS → TVD → MD`, renderability, MARKER/HORIZON lines және warnings.
- ✅ synthetic demo dataset және coordinate-тан cross-section-ға дейінгі `POST /api/v1/correlation/demo/workflow`.
- ✅ external RAW/staging, checksum, SyncRun және ExternalEntityLink.
- ✅ Kazakhstan Open Data API v4 connector, `stat_kgn_117/v10` және `zher_koinauyn_geologiyalyk_zer2/v6` registry.
- ✅ oil/gas field normalization, safe matching, review queue/actions және RU/KK/EN review UI contract.
- ✅ dedicated external sync scheduler, due/retry, row-lock protection және Update All.
- ✅ persistent organization/local CRS registry: `organization_crs_definitions`, migration `20260904_0005`.
- ✅ local CRS нақты `EPSG`, `WKT` немесе `PROJ`, canonical WKT және `source_reference` сақтайды.
- ✅ explicit confirmation workflow; тек active + `is_confirmed=true` entry `registered_crs_code` арқылы қолданылады.
- ✅ definition/axis order/source reference өзгерсе confirmation автоматты түрде жойылады.
- ✅ spatial nearby және demo correlation registry-aware coordinate resolution қолданады; unconfirmed CRS блокталады.
- ✅ local CRS registry unit tests және нақты PostgreSQL/PostGIS API integration test арқылы тексерілді.
- ✅ `LOCAL_CRS_REGISTRY_*` RU/KK/EN documentation қосылды.

## Тұрақты API contracts
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — RAW field normalize + match.
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review` — technical review queue.
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` — UI-ready review view-model.
- `POST /api/v1/integrations/sync-all` — manual Update All.
- `GET /api/v1/integrations/scheduler/status` — scheduler state.
- `POST /api/v1/integrations/scheduler/run-due` — scheduled-due pass.
- `POST /api/v1/correlation/wells/view` — visual cross-section view-model.
- `POST /api/v1/correlation/demo/workflow` — complete synthetic demo workflow.
- `GET /api/v1/spatial/crs-definitions` — organization CRS list.
- `POST /api/v1/spatial/crs-definitions` — unconfirmed CRS create.
- `POST /api/v1/spatial/crs-definitions/{definition_id}/confirm` — explicit confirmation.

## Жақын P0
1. Correlation distance query ішіндегі қалған SQLAlchemy cartesian-product warning-ті PostGIS distance нәтижесін өзгертпей жою.
2. Lithology/markers/property kinds/units controlled vocabularies.
3. Геологиялық лицензиялар resource үшін mapping/license/data quality тексерілгеннен кейін normalizer/review қосу.
4. Core Dataset manifest/importer.
5. Review, CRS confirmation және master-data changes үшін Authentication + AuditLog/revisions.
6. Stable backend view-model негізінде production PySide6 external-review screen.
7. USGS/Macrostrat/OneGeology providers тек license/contract тексерілгеннен кейін кеңейтіледі.

## Релиздер
- `v0.2`: platform/evidence/integration/spatial/subsurface/correlation foundation және алғашқы Kazakhstan Open Data integrations — `main` ішінде.
- `v0.3`: review UI, scheduled sync, visual cross-section, complete demo workflow және persistent local CRS registry.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y import.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + production visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
User-facing функция implementation, validation, tests, қажет migration, RU/KK/EN docs/help, provenance/verification rules және green CI болғанда ғана аяқталған болып саналады.
