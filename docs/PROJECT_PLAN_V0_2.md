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
- ✅ external integration foundation и Kazakhstan Open Data API v4 connector.
- ✅ USER_GUIDE и roadmap на RU/KK/EN + documentation CI contract.

## Ближайший P0
1. API/view-model для визуального cross-section viewer: колонки скважин, шкала глубин, реперы, интервалы и линии корреляции.
2. Demo workflow в приложении: координата → 4 ближайшие demo-скважины → выбор → корреляционный разрез.
3. Хранение/настройка локальных CRS организации; СК-42/Гаусса–Крюгера только по подтверждённому EPSG/WKT/PROJ.
4. Устранить SQLAlchemy cartesian-product warning в distance query корреляции.
5. Controlled vocabularies для lithology/markers/property kinds/units.
6. External sync persistence + manual/scheduled sync.
7. Registry официальных Kazakhstan Open Data datasets.
8. Core Dataset manifest/importer.
9. Audit log/revisions.

## Релизы
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation.
- `v0.3`: visual correlation data contract, CRS/local settings, complete demo workflow.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: scheduled sync/matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пользовательская функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN help/docs, provenance/verification и зелёного CI.
