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
- ✅ ресми naming contract: `apiUri` + `version`; RAW technical fields өзгертілмейді, GeoKZ `code` және `record_type` upstream identifiers-тен бөлек сақталады.
- ✅ connector ресми `/meta/{apiUri}/{version}` және `/api/v4/mapping/{apiUri}/{version}` endpoint-терін импортқа дейін оқиды.
- ✅ `GET /api/v1/integrations/kazakhstan/catalog` — `api_uri`, version және endpoint templates бар ресми каталог.
- ✅ `GET /api/v1/integrations/kazakhstan/{code}/schema` — external metadata/mapping тексеру endpoint-і.
- ✅ `POST /api/v1/integrations/kazakhstan/register` — дереккөздерді жергілікті GeoKZ БД-сына тіркеу.
- ✅ `POST /api/v1/integrations/kazakhstan/{code}/sync` — RAW/staging қабатына қолмен REST-синхрондау.
- ✅ `stat_kgn_117` normalizer тек dataset растайтын кен орны атауын шығарады; RAW өзгертілмейді.
- ✅ мұнай-газ кен орындарын `GeologicalEntity(object_type="field")` және `EntityName` aliases арқылы matching.
- ✅ exact/alias matches тек `ExternalEntityLink(status=REVIEW_REQUIRED)` жасайды; ambiguous/unmatched review үшін сақталады; reviewer қойған VERIFIED/REJECTED links автоматты түрде өзгертілмейді.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — RAW sync кейін normalize + match.
- ✅ дереккөздер `AUTOMATIC`, 168 сағаттық интервалмен тіркеледі; нақты scheduler әлі іске асырылмаған.
- ✅ API key тек `GEOKZ_EGOV_API_KEY` арқылы оқылады; кілт болмаса жергілікті база жұмысын жалғастырады.
- ✅ API кілттерін алу және баптау туралы RU/KK/EN нұсқаулықтары.
- ✅ Kazakhstan Open Data resource naming және connection туралы RU/KK/EN жеке нұсқаулықтар.
- ✅ README ішінде API key, `apiUri` contract, processing endpoint және resource onboarding ережелері бар.
- ✅ RU/KK/EN user guides/roadmaps және documentation CI contract.

## Жақын P0
1. Visual cross-section viewer үшін API/view-model: ұңғыма бағандары, depth scale, реперлер, интервалдар және correlation lines.
2. Demo workflow: координата → 4 жақын demo-ұңғыма → таңдау → correlation section.
3. Ұйымның local CRS сақтау/баптау; СК-42/Гаусс–Крюгер тек расталған EPSG/WKT/PROJ арқылы.
4. Correlation distance query ішіндегі SQLAlchemy cartesian-product warning-ті жою.
5. Lithology/markers/property kinds/units controlled vocabularies.
6. Сыртқы дереккөздерді мерзімді синхрондау scheduler-і және «Барлығын жаңарту» функциясы.
7. `ExternalEntityLink` үшін review API/UI: confirm, reject, manual link және unmatched candidate-тан жаңа DRAFT field тек пайдаланушының нақты әрекетімен жасалады.
8. Metadata/mapping/license/data quality тексерілгеннен кейін келесі ресми Қазақстан resources қосу; келесі кандидат — геологиялық лицензиялар.
9. Core Dataset manifest/importer.
10. Audit log/revisions.

## Релиздер
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + Қазақстанның алғашқы ресми REST integrations + safe oil/gas-field normalization/matching.
- `v0.3`: visual correlation data contract, CRS/local settings, complete demo workflow, scheduled external sync және review workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: external source matching/review/audit кеңейту.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пайдаланушы функциясы implementation, validation, tests, қажет migration, RU/KK/EN help/docs, provenance/verification және жасыл CI болған кезде ғана аяқталған болып есептеледі.
