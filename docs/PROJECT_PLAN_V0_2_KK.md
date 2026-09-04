# GeoKZ — v0.2+ өзекті даму жоспары

Мәртебе: `2026-09-04`, тармақ `feature/external-data-sync-v0.2`.

## Мақсаты
GeoKZ — Қазақстан геологиясы бойынша бірыңғай жұмыс терезесі: аумақ/координата → кен орындары мен ұңғымалар → толық паспорт → литология/стратиграфия/ҰГЗ/керн/сынақ/мұнай-газ-су → көршілес ұңғымалар корреляциясы → дереккөз және дәлел.

## Міндетті қағидалар
- RU/KK/EN барлық пайдаланушы функциялары мен құжаттамасында.
- Verified data сыртқы API немесе AI арқылы review-сіз өзгертілмейді.
- RAW, бастапқы құжаттар, LAS/DLIS/SEG-Y интерпретациядан бөлек сақталады.
- CRS, axis order, MD/TVD/TVDSS және units әрқашан анық көрсетіледі.
- Core Dataset интернетсіз де жұмыс істейді.
- Demo/synthetic деректер өндірістік факт ретінде пайдаланылмайды және айқын белгіленеді.

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
- ✅ exact/alias candidates `REVIEW_REQUIRED`; ambiguous/unmatched review үшін сақталады; reviewer-locked links қайта process кезінде өзгертілмейді.
- ✅ review queue: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ review actions: candidate confirm/reject, existing field-пен `manual-link`, тек `UNMATCHED` үшін explicit `create-draft-field`.
- ✅ сыртқы record-тан жасалған жаңа `GeologicalEntity` тек `DRAFT`; verified link объектіні автоматты түрде VERIFIED етпейді.
- ✅ reviewer және comment ExternalEntityLink ішінде сақталады; толық authentication/AuditLog кейін қосылады.
- ✅ sources `AUTOMATIC`, 168 сағаттық interval; нақты scheduler әлі жоқ.
- ✅ API key тек `GEOKZ_EGOV_API_KEY` арқылы оқылады.
- ✅ API keys, Open Data onboarding/naming және field review үшін RU/KK/EN құжаттары бар.
- ✅ README, user guides және roadmaps documentation CI арқылы бақыланады.

## Жақын P0
1. Қазіргі review backend-ті PostgreSQL/PostGIS CI-де толық жасыл күйге жеткізу және review queue UI contract жасау.
2. Scheduled external sync + «Барлығын жаңарту».
3. Visual cross-section viewer API/view-model және demo workflow.
4. Ұйымның configurable local CRS жүйелері.
5. Correlation distance query ішіндегі SQLAlchemy cartesian-product warning-ті жою.
6. Lithology/markers/property kinds/units controlled vocabularies.
7. Геологиялық лицензиялар ресурсына normalizer/review қосу — mapping/license/data quality тексерілгеннен кейін.
8. Core Dataset manifest/importer.
9. Authentication + AuditLog/revisions.
10. Кейінгі production PySide6 review және integration UI.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation + алғашқы Kazakhstan REST integrations + safe oil/gas-field normalization/matching/review.
- `v0.3`: visual correlation contract, CRS/local settings, complete demo workflow, scheduled sync және review UI.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пайдаланушы функциясы implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған болып есептеледі.
