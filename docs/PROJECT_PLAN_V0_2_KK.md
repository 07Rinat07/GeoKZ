# GeoKZ — v0.2+ өзекті даму жоспары

Мәртебе: `2026-09-04`, тармақ `feature/demo-correlation-workflow-v0.3`.

## Мақсаты
GeoKZ — Қазақстан геологиясы бойынша бірыңғай жұмыс терезесі: аумақ/координата → кен орындары мен ұңғымалар → паспорт → интервалдар/литология/ҰГЗ/керн/сынақ → корреляция → дереккөз және дәлел.

## Негізгі қағидалар
- RU/KK/EN барлық пайдаланушы функциялары мен құжаттамасында.
- Verified data сыртқы API немесе AI арқылы review-сіз өзгертілмейді.
- CRS, axis order және MD/TVD/TVDSS анық көрсетіледі.
- Demo/synthetic деректер production facts ретінде қолданылмайды.
- UI backend business rules пен correlation/depth logic-ті қайталамайды.
- Periodic external sync dedicated process/service арқылы іске қосылады.

## Іске асырылды
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic және PostgreSQL/PostGIS CI.
- ✅ Territory Explorer, Geological Entity Passport, Well Passport.
- ✅ `POST /api/v1/spatial/nearby`, coordinate resolver және CRS helper.
- ✅ trajectory, logs, tests, core, seismic және Well Correlation.
- ✅ Kazakhstan Open Data connector, RAW/staging, checksum, source registry және review workflow.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process`.
- ✅ `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` және backend-owned action descriptors.
- ✅ `POST /api/v1/integrations/sync-all`, `POST /api/v1/integrations/scheduler/run-due`, `GET /api/v1/integrations/scheduler/status`.
- ✅ dedicated external scheduler және PostgreSQL parallel-run protection.
- ✅ visual cross-section: `POST /api/v1/correlation/wells/view`.
- ✅ depth axis `TVDSS → TVD → MD`, `renderable=false`, `MARKER`/`HORIZON` lines және stable warnings.
- ✅ complete demo workflow: `POST /api/v1/correlation/demo/workflow`.
- ✅ алғашқы request `stage=DISCOVERY`, `nearby_demo_wells`, suggested reference және selection contract қайтарады.
- ✅ `reference_well_id` + `well_ids` бар екінші request `stage=CROSS_SECTION_READY` және дайын `cross_section` қайтарады.
- ✅ demo selection тек `synthetic-correlation-demo-v1` dataset well-деріне рұқсат береді; кәдімгі production well координатасы сәйкес болса да кірмейді.
- ✅ incomplete, duplicate немесе discovery тізімінен тыс selection HTTP `422` арқылы қабылданбайды.
- ✅ demo dataset `python -m scripts.seed_correlation_demo` арқылы жасалады.
- ✅ complete demo HTTP path нақты PostgreSQL/PostGIS integration test арқылы тексеріледі.
- ✅ RU/KK/EN user guides, roadmaps және feature contracts documentation CI арқылы тексеріледі.

## Жақын P0
1. Ұйымның configurable local CRS жүйелері; СК-42/Гаусс–Крюгер тек расталған EPSG/WKT/PROJ арқылы.
2. Correlation distance query ішіндегі SQLAlchemy cartesian-product warning-ті PostGIS distance нәтижесін өзгертпей жою.
3. Lithology/markers/property kinds/units controlled vocabularies.
4. Геологиялық лицензиялар ресурсына normalizer/review қосу.
5. Core Dataset manifest/importer.
6. Authentication + AuditLog/revisions.
7. Production PySide6 external review screen.
8. USGS/Macrostrat/OneGeology provider registry — licence/contract тексерілгеннен кейін.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation және алғашқы Kazakhstan integrations.
- `v0.3`: review UI contract, scheduler/Update All, visual correlation contract, complete synthetic demo workflow және CRS/local settings.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Функция implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған деп саналады.
