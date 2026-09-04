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
- ✅ `POST /api/v1/spatial/nearby` для поиска ближайших объектов, скважин и сейсмики.
- ✅ модели trajectory, well logs, tests, core, seismic.
- ✅ Well Correlation: WellMarker, TVDSS-preferred comparison, реперы, интервалы, thickness/net pay, porosity/permeability, lithology/fluid/hydrocarbon differences.
- ✅ реальный PostGIS integration test корреляции.
- ✅ синтетический demo-набор: 4 соседние скважины, R1/R2, J-II.
- ✅ external integration foundation и Kazakhstan Open Data API v4 connector.
- ✅ USER_GUIDE и roadmap на RU/KK/EN + documentation CI contract.

## Ближайший P0
1. Связать coordinate search → выбор ближайших скважин → запуск корреляции.
2. Integration test полного `POST /api/v1/spatial/nearby` workflow.
3. Каталог CRS Казахстана и настраиваемые локальные CRS.
4. Устранить SQLAlchemy warning в distance query корреляции.
5. API-модель для визуального cross-section viewer.
6. Demo workflow: координата → 4 скважины → корреляция.
7. External sync persistence + manual/scheduled sync.
8. Registry официальных Kazakhstan Open Data datasets.
9. Core Dataset manifest/importer.
10. Controlled vocabularies + audit/revisions.

## Релизы
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
Пользовательская функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN help/docs, provenance/verification и зелёного CI.
