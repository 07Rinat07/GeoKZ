# GeoKZ — v0.2+ өзекті даму жоспары

Мәртебе: `2026-09-04`, тармақ `feature/external-review-ui-contract-v0.3`. v0.2 негізі жасыл CI-ден кейін `main` тармағына біріктірілді.

## Мақсаты
GeoKZ — Қазақстан геологиясы бойынша бірыңғай жұмыс терезесі: аумақ/координата → кен орындары мен ұңғымалар → толық паспорт → литология/стратиграфия/ҰГЗ/керн/сынақ/мұнай-газ-су → көршілес ұңғымалар корреляциясы → дереккөз және дәлел.

## Міндетті қағидалар
- RU/KK/EN барлық пайдаланушы функциялары мен құжаттамасында.
- Verified data сыртқы API немесе AI арқылы review-сіз өзгертілмейді.
- RAW, бастапқы құжаттар, LAS/DLIS/SEG-Y интерпретациядан бөлек сақталады.
- CRS, axis order, MD/TVD/TVDSS және units әрқашан анық көрсетіледі.
- Core Dataset интернетсіз де жұмыс істейді.
- Demo/synthetic деректер өндірістік факт ретінде пайдаланылмайды және айқын белгіленеді.
- UI backend business rules логикасын қайталамайды: review action availability және required fields backend view-model арқылы беріледі.

## Іске асырылды
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic.
- ✅ RU/KK/EN About/Help және автор Sarmuldin Rinat / ura07srr@gmail.com.
- ✅ PostgreSQL/PostGIS CI: таза БД, `0001 → 0004` миграциялары, PostGIS/pg_trgm/unaccent, geography distance.
- ✅ Territory Explorer, Geological Entity Passport, Well Passport.
- ✅ latitude/longitude және projected X/Y; нүкте/үтір; CRS; екі X/Y axis order.
- ✅ pyproj/PROJ `CoordinateResolver`, WGS84 түрлендіруі және `POST /api/v1/spatial/nearby`.
- ✅ trajectory, well logs, tests, core, seismic модельдері және Well Correlation.
- ✅ synthetic demo dataset: 4 көршілес ұңғыма, R1/R2, J-II.
- ✅ external integration foundation: RAW/staging, checksum, SyncRun және ExternalEntityLink.
- ✅ Kazakhstan Open Data API v4 connector, ресми `apiUri` + `version`, metadata/mapping inspection.
- ✅ `stat_kgn_117/v10` және `zher_koinauyn_geologiyalyk_zer2/v6` registry.
- ✅ catalog/register/schema/sync REST endpoints.
- ✅ `stat_kgn_117` normalizer және `GeologicalEntity(object_type="field")` / `EntityName` aliases matching.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — RAW sync кейін normalize + match.
- ✅ exact/alias candidates `REVIEW_REQUIRED`; ambiguous/unmatched review үшін сақталады.
- ✅ қайталанған `process` unresolved auto-links үшін идемпотентті және duplicate `ExternalEntityLink` жасамайды.
- ✅ reviewer-locked links (`VERIFIED`, `REJECTED`, `MANUAL`, reviewer/comment) қайта process кезінде өзгертілмейді.
- ✅ техникалық review queue: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ review actions: candidate confirm/reject, existing field-пен `manual-link`, тек `UNMATCHED` үшін explicit `create-draft-field`.
- ✅ сыртқы record-тан жасалған жаңа `GeologicalEntity` тек `DRAFT`; verified link объектіні автоматты түрде VERIFIED етпейді.
- ✅ reviewer және comment ExternalEntityLink ішінде сақталады; толық authentication/AuditLog кейін қосылады.
- ✅ review/matching backend бір head-та жасыл `Python quality checks` және PostgreSQL/PostGIS integration tests арқылы расталып, `main` тармағына біріктірілді.
- ✅ review queue UI/view-model contract: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`.
- ✅ view-model RU/KK/EN title/policy note, `total_pending`, pagination, локализацияланған candidate name, жеке `entity_verification_status` және тұрақты `matching_status` қайтарады.
- ✅ `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD` action descriptor-лары `enabled`, `disabled_reason`, `required_fields`, `optional_fields` және нақты `path` береді.
- ✅ `UNKNOWN` matching status болашақ жаңа мәндер үшін safe fallback.
- ✅ review view-model үшін unit tests және нақты PostgreSQL HTTP integration test қосылды.
- ✅ sources `AUTOMATIC`, 168 сағаттық interval; нақты scheduler әлі жоқ.
- ✅ API key тек `GEOKZ_EGOV_API_KEY` арқылы оқылады.
- ✅ API keys, Open Data onboarding/naming, field review және review UI contract үшін RU/KK/EN құжаттары бар.
- ✅ README, user guides және roadmaps documentation CI арқылы бақыланады.

## Жақын P0
1. Scheduled external sync + «Барлығын жаңарту», параллель sync іске қосылуынан қорғау және әр source үшін status/error reporting.
2. Visual cross-section viewer API/view-model: well columns, depth scale, markers, intervals және correlation lines.
3. Координата → жақын demo-ұңғымалар → таңдау → correlation section толық сценарийі.
4. Ұйымның configurable local CRS жүйелері; СК-42/Гаусс–Крюгер тек расталған EPSG/WKT/PROJ арқылы.
5. Correlation distance query ішіндегі қалған SQLAlchemy cartesian-product warning-ті PostGIS distance нәтижесін өзгертпей жою.
6. Lithology/markers/property kinds/units controlled vocabularies.
7. Геологиялық лицензиялар ресурсына normalizer/review қосу — mapping/license/data quality тексерілгеннен кейін.
8. Core Dataset manifest/importer.
9. Review және master data өзгерістері үшін Authentication + AuditLog/revisions.
10. Тұрақты backend view-model негізінде production PySide6 external review screen.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation + алғашқы Kazakhstan REST integrations + safe oil/gas-field normalization/matching/review — `main` тармағына біріктірілді.
- `v0.3`: review UI contract, visual correlation contract, CRS/local settings, complete demo workflow және scheduled sync.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пайдаланушы функциясы implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған болып есептеледі.
