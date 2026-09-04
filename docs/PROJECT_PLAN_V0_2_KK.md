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
- ✅ pyproj/PROJ негізіндегі `CoordinateResolver`, WGS84 түрлендіруі.
- ✅ `POST /api/v1/spatial/nearby` — жақын объектілерді, ұңғымаларды және сейсмиканы іздеу.
- ✅ `/api/v1/spatial/nearby` HTTP integration test нақты PostGIS базасында өтті.
- ✅ trajectory, well logs, tests, core, seismic модельдері.
- ✅ Well Correlation: реперлер, TVDSS, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ нақты PostGIS correlation integration test.
- ✅ 4 көршілес ұңғымадан, R1/R2 және J-II-ден тұратын synthetic demo dataset.
- ✅ Kazakhstan Open Data API v4 connector және external integration foundation.
- ✅ RU/KK/EN user guides/roadmaps және documentation CI contract.

## Жақын P0
1. Coordinate search нәтижесін жақын ұңғымаларды таңдаумен және correlation іске қосумен байланыстыру.
2. Қазақстан CRS каталогы және ұйымның local CRS баптауы.
3. Correlation distance query ішіндегі SQLAlchemy warning-ті жою.
4. Visual cross-section viewer үшін API data model.
5. Demo workflow: координата → 4 ұңғыма → корреляция.
6. External sync persistence + manual/scheduled sync.
7. Ресми Kazakhstan Open Data dataset registry.
8. Core Dataset manifest/importer.
9. Controlled vocabularies + audit/revisions.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation.
- `v0.3`: coordinate/CRS hardening + correlation demo workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: scheduled sync/matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пайдаланушы функциясы implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған болып есептеледі.
