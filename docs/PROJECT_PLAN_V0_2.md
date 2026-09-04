# GeoKZ — актуальный план развития v0.2+

Статус: `2026-09-04`, ветка `feature/local-crs-registry-v0.3`.

## Цель
GeoKZ — доказательная геологическая информационная система Казахстана: территория/координата → объект → скважина → интервалы/каротаж/керн/испытания → корреляция → источник и доказательство.

## Обязательные правила
- RU/KK/EN во всём пользовательском продукте и документации.
- Verified master data не изменяются внешним API или AI без review.
- RAW и исходные документы хранятся отдельно от интерпретации.
- CRS, axis order, MD/TVD/TVDSS и units всегда явные.
- Core Dataset работает без обязательного интернета.
- Synthetic/demo данные отделены от production data.
- UI не дублирует backend business rules.
- Periodic external sync работает отдельным process/service.

## Реализовано
- ✅ FastAPI + PostgreSQL/PostGIS + SQLAlchemy async + Alembic.
- ✅ PostgreSQL/PostGIS CI с миграциями, PostGIS, pg_trgm и unaccent.
- ✅ Territory Explorer, Geological Entity Passport и Well Passport.
- ✅ geographic/projected coordinate input, WGS84/UTM helper и pyproj/PROJ resolution.
- ✅ `POST /api/v1/spatial/nearby` и реальный PostGIS integration test.
- ✅ trajectory, well logs, tests, core, seismic и Well Correlation.
- ✅ `POST /api/v1/correlation/wells` и backend-owned `POST /api/v1/correlation/wells/view`.
- ✅ безопасный visual cross-section contract: `TVDSS → TVD → MD`, renderability, MARKER/HORIZON lines, warnings.
- ✅ synthetic demo dataset и полный `POST /api/v1/correlation/demo/workflow` от координаты до cross-section.
- ✅ external integration foundation: RAW/staging, checksum, SyncRun, ExternalEntityLink.
- ✅ Kazakhstan Open Data API v4 connector и registry `stat_kgn_117/v10`, `zher_koinauyn_geologiyalyk_zer2/v6`.
- ✅ oil/gas field normalization, safe matching, review queue/actions и RU/KK/EN review UI contract.
- ✅ dedicated external sync scheduler, due/retry, row-lock protection и Update All.
- ✅ persistent organization/local CRS registry: `organization_crs_definitions`, миграция `20260904_0005`.
- ✅ локальные CRS принимают точные `EPSG`, `WKT` или `PROJ`, сохраняют canonical WKT и `source_reference`.
- ✅ explicit confirm workflow; только active + `is_confirmed=true` запись используется через `registered_crs_code`.
- ✅ изменение definition/axis order/source reference автоматически снимает confirmation.
- ✅ spatial nearby и demo correlation используют registry-aware coordinate resolution; неподтверждённая CRS блокируется.
- ✅ local CRS registry покрыт unit tests и реальным PostgreSQL/PostGIS API integration test.
- ✅ отдельная RU/KK/EN документация `LOCAL_CRS_REGISTRY_*`.

## Ближайший P0
1. Устранить оставшийся SQLAlchemy cartesian-product warning в correlation distance query без изменения результата PostGIS distance.
2. Controlled vocabularies для lithology/markers/property kinds/units.
3. Добавить normalizer/review для ресурса геологических лицензий после проверки mapping/license/data quality.
4. Core Dataset manifest/importer.
5. Authentication + AuditLog/revisions для review, CRS confirmation и master-data changes.
6. Production PySide6 external-review screen на стабильном backend view-model contract.
7. Расширять providers на USGS/Macrostrat/OneGeology только после проверки лицензий и контрактов.

## Релизы
- `v0.2`: platform, evidence/integration, spatial/subsurface/correlation foundation и первые Kazakhstan Open Data integrations — слито в `main`.
- `v0.3`: review UI, scheduled sync, visual cross-section, complete demo workflow и persistent local CRS registry.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y import.
- `v0.5`: expanded external matching/review/audit.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + production visual correlation viewer.
- `v0.8`: geological-model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN docs/help, provenance/verification rules и зелёного CI.
