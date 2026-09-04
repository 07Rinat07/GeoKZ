# GeoKZ — актуальный план развития v0.2+

Статус: `2026-09-04`, ветка `feature/external-data-sync-v0.2`.

## Цель
GeoKZ — единое рабочее окно по геологии Казахстана: территория/координата → месторождения и скважины → полный паспорт → литология/стратиграфия/ГИС/керн/испытания/нефть-газ-вода → корреляция соседних скважин → источник и доказательство.

## Обязательные правила
- RU/KK/EN во всём пользовательском продукте и документации.
- Проверенные данные не перезаписываются внешними API или ИИ без review.
- Исходные документы/RAW/LAS/DLIS/SEG-Y сохраняются отдельно от интерпретации.
- CRS, axis order, MD/TVD/TVDSS и units всегда явные.
- Core Dataset работает без обязательного интернета.
- Demo/synthetic данные явно маркируются и не считаются производственными фактами.

## Реализовано
- ✅ FastAPI + PostgreSQL/PostGIS + Alembic.
- ✅ RU/KK/EN About/Help и автор Sarmuldin Rinat / ura07srr@gmail.com.
- ✅ PostgreSQL/PostGIS CI: чистая БД, миграции `0001 → 0004`, PostGIS/pg_trgm/unaccent, geography distance.
- ✅ Territory Explorer, Geological Entity Passport, Well Passport.
- ✅ координаты: latitude/longitude и projected X/Y; точка/запятая; CRS; два порядка X/Y.
- ✅ `CoordinateResolver` на pyproj/PROJ и преобразование в WGS84.
- ✅ `POST /api/v1/spatial/nearby` + HTTP integration test на реальной PostGIS.
- ✅ CRS helper API `GET /api/v1/spatial/crs-presets`: WGS84 и UTM 38N–45N, RU/KK/EN предупреждения; CRS не угадывается автоматически.
- ✅ модели trajectory, well logs, tests, core, seismic.
- ✅ Well Correlation: реперы, TVDSS, интервалы, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ `POST /api/v1/correlation/wells` для выбранной опорной и соседних скважин; GET оставлен совместимым.
- ✅ POST correlation проверяется на реальной PostGIS базе.
- ✅ synthetic demo dataset: 4 соседние скважины, R1/R2, J-II.
- ✅ external integration foundation: RAW/staging, checksum, SyncRun, source status и безопасное обновление.
- ✅ универсальный Kazakhstan Open Data API v4 connector.
- ✅ официальный registry Kazakhstan Open Data: `stat_kgn_117/v10` (нефтегазовые месторождения) и `zher_koinauyn_geologiyalyk_zer2/v6` (лицензии на геологическое изучение недр).
- ✅ `GET /api/v1/integrations/kazakhstan/catalog` — каталог официальных наборов.
- ✅ `POST /api/v1/integrations/kazakhstan/register` — регистрация источников в локальной БД.
- ✅ `POST /api/v1/integrations/kazakhstan/{code}/sync` — ручная REST-синхронизация в RAW/staging.
- ✅ источники регистрируются как `AUTOMATIC` с интервалом 168 часов; фактический scheduler ещё не реализован.
- ✅ API key хранится только в `GEOKZ_EGOV_API_KEY`; без ключа локальная база продолжает работать.
- ✅ отдельные инструкции по получению/настройке API-ключей на RU/KK/EN: `EXTERNAL_API_KEYS_RU.md`, `EXTERNAL_API_KEYS_KK.md`, `EXTERNAL_API_KEYS_EN.md`.
- ✅ README содержит краткую инструкцию по получению ключа `data.egov.kz` и безопасной настройке `.env`.
- ✅ USER_GUIDE и roadmap на RU/KK/EN + documentation CI contract.

## Ближайший P0
1. API/view-model для визуального cross-section viewer: колонки скважин, шкала глубин, реперы, интервалы и линии корреляции.
2. Demo workflow в приложении: координата → 4 ближайшие demo-скважины → выбор → корреляционный разрез.
3. Хранение/настройка локальных CRS организации; СК-42/Гаусса–Крюгера только по подтверждённому EPSG/WKT/PROJ.
4. Устранить SQLAlchemy cartesian-product warning в distance query корреляции.
5. Controlled vocabularies для lithology/markers/property kinds/units.
6. Scheduler периодической синхронизации внешних источников и кнопка «Обновить всё».
7. Нормализация и matching записей Kazakhstan Open Data с GeologicalEntity/месторождениями GeoKZ.
8. Добавление следующих официальных наборов Казахстана после проверки схемы/лицензии/качества данных.
9. Core Dataset manifest/importer.
10. Audit log/revisions.

## Релизы
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + первые официальные REST integrations Казахстана.
- `v0.3`: visual correlation data contract, CRS/local settings, complete demo workflow, scheduled external sync.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: matching/review/audit для внешних источников.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пользовательская функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN help/docs, provenance/verification и зелёного CI.