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
- ✅ pyproj/PROJ `CoordinateResolver`, WGS84 түрлендіруі.
- ✅ `POST /api/v1/spatial/nearby` және нақты PostGIS HTTP integration test.
- ✅ `GET /api/v1/spatial/crs-presets`: WGS84, UTM 38N–45N, RU/KK/EN ескерту; CRS автоматты түрде болжанбайды.
- ✅ trajectory, well logs, tests, core, seismic модельдері.
- ✅ Well Correlation: реперлер, TVDSS, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ `POST /api/v1/correlation/wells` — тірек және таңдалған көршілес ұңғымалар үшін; GET үйлесімділік үшін сақталды.
- ✅ POST correlation нақты PostGIS базасында тексеріледі.
- ✅ 4 көршілес ұңғыма, R1/R2 және J-II бар synthetic demo dataset.
- ✅ external integration foundation: RAW/staging, checksum, SyncRun, source status және қауіпсіз жаңарту.
- ✅ Kazakhstan Open Data API v4 үшін әмбебап connector.
- ✅ ресми Kazakhstan Open Data registry: `stat_kgn_117/v10` (мұнай-газ кен орындары) және `zher_koinauyn_geologiyalyk_zer2/v6` (геологиялық зерттеу лицензиялары).
- ✅ `GET /api/v1/integrations/kazakhstan/catalog` — ресми dataset каталогы.
- ✅ `POST /api/v1/integrations/kazakhstan/register` — дереккөздерді жергілікті GeoKZ БД-сына тіркеу.
- ✅ `POST /api/v1/integrations/kazakhstan/{code}/sync` — RAW/staging қабатына қолмен REST-синхрондау.
- ✅ дереккөздер `AUTOMATIC`, 168 сағаттық интервалмен тіркеледі; нақты scheduler әлі іске асырылмаған.
- ✅ API key тек `GEOKZ_EGOV_API_KEY` арқылы оқылады; кілт болмаса жергілікті база жұмысын жалғастырады.
- ✅ API кілттерін алу және баптау туралы RU/KK/EN нұсқаулықтары: `EXTERNAL_API_KEYS_RU.md`, `EXTERNAL_API_KEYS_KK.md`, `EXTERNAL_API_KEYS_EN.md`.
- ✅ README ішінде `data.egov.kz` кілтін алу және `.env` ішінде қауіпсіз сақтау жөніндегі қысқа нұсқаулық бар.
- ✅ RU/KK/EN user guides/roadmaps және documentation CI contract.

## Жақын P0
1. Visual cross-section viewer үшін API/view-model: ұңғыма бағандары, depth scale, реперлер, интервалдар және correlation lines.
2. Demo workflow: координата → 4 жақын demo-ұңғыма → таңдау → correlation section.
3. Ұйымның local CRS сақтау/баптау; СК-42/Гаусс–Крюгер тек расталған EPSG/WKT/PROJ арқылы.
4. Correlation distance query ішіндегі SQLAlchemy cartesian-product warning-ті жою.
5. Lithology/markers/property kinds/units controlled vocabularies.
6. Сыртқы дереккөздерді мерзімді синхрондау scheduler-і және «Барлығын жаңарту» функциясы.
7. Kazakhstan Open Data жазбаларын GeoKZ GeologicalEntity/кен орындарымен нормализациялау және matching.
8. Схемасы, лицензиясы және сапасы тексерілгеннен кейін Қазақстанның келесі ресми dataset-терін қосу.
9. Core Dataset manifest/importer.
10. Audit log/revisions.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + Қазақстанның алғашқы ресми REST integrations.
- `v0.3`: visual correlation data contract, CRS/local settings, complete demo workflow, scheduled external sync.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: external source matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пайдаланушы функциясы implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған болып есептеледі.