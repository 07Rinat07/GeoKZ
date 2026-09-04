# GeoKZ — актуальный план развития v0.2+

Статус: `2026-09-04`, ветка `feature/demo-correlation-workflow-v0.3`. Фундамент v0.2, review UI contract, dedicated external-sync scheduler и visual cross-section view-model уже слиты в `main` после зелёного CI.

## Цель
GeoKZ — единое рабочее окно по геологии Казахстана: территория/координата → месторождения и скважины → полный паспорт → литология/стратиграфия/ГИС/керн/испытания/нефть-газ-вода → корреляция соседних скважин → источник и доказательство.

## Обязательные правила
- RU/KK/EN во всём пользовательском продукте и документации.
- Проверенные данные не перезаписываются внешними API или ИИ без review.
- Исходные документы/RAW/LAS/DLIS/SEG-Y сохраняются отдельно от интерпретации.
- CRS, axis order, MD/TVD/TVDSS и units всегда явные.
- Core Dataset работает без обязательного интернета.
- Demo/synthetic данные явно маркируются и не считаются производственными фактами.
- UI не дублирует backend business rules: доступность review-действий и обязательные поля задаёт backend view-model.
- Periodic external sync работает отдельным process/service, не background loop внутри каждого FastAPI worker.

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
- ✅ официальный registry Kazakhstan Open Data: `stat_kgn_117/v10` и `zher_koinauyn_geologiyalyk_zer2/v6`.
- ✅ официальный контракт `apiUri` + `version`; RAW fields сохраняются без переименования.
- ✅ metadata/mapping inspection до импорта и REST catalog/register/sync/schema endpoints.
- ✅ `stat_kgn_117` normalizer и matching с `GeologicalEntity(object_type="field")`/`EntityName` aliases.
- ✅ `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — normalize + match после RAW sync.
- ✅ автоматические exact/alias matches остаются `REVIEW_REQUIRED`; ambiguous/unmatched сохраняются для review.
- ✅ повторный `process` идемпотентен для незавершённых auto-links и не создаёт дубли `ExternalEntityLink`.
- ✅ reviewer-locked links (`VERIFIED`, `REJECTED`, `MANUAL`, reviewer/comment) не перезаписываются повторным process.
- ✅ техническая review queue: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review`.
- ✅ review actions: confirm/reject candidate, manual-link к существующему field, explicit `create-draft-field` только для `UNMATCHED`.
- ✅ новый объект из внешней записи создаётся только `GeologicalEntity(verification_status=DRAFT)`; verified link не делает объект VERIFIED.
- ✅ reviewer identity/comment сохраняются в `ExternalEntityLink`; полноценные auth/AuditLog ещё запланированы.
- ✅ UI/view-model contract очереди review: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`.
- ✅ action descriptors `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD` содержат backend-owned availability/form contract.
- ✅ scheduler периодической внешней синхронизации реализован отдельным process/service `python -m scripts.external_sync_scheduler`.
- ✅ ручное «Обновить всё»: `POST /api/v1/integrations/sync-all`.
- ✅ scheduled due dispatch: `POST /api/v1/integrations/scheduler/run-due`; status: `GET /api/v1/integrations/scheduler/status`.
- ✅ PostgreSQL row-lock/stale-run защита parallel sync.
- ✅ backend-owned visual cross-section view-model: `POST /api/v1/correlation/wells/view`.
- ✅ единая шкала глубин выбирается по приоритету `TVDSS → TVD → MD`; несовместимые элементы получают `renderable=false`.
- ✅ response содержит ordered well columns, depth axis, готовые `MARKER`/`HORIZON` line segments и stable warnings.
- ✅ complete synthetic demo workflow: `POST /api/v1/correlation/demo/workflow`.
- ✅ первый вызов workflow выполняет coordinate resolution + PostGIS discovery и возвращает `stage=DISCOVERY`, `nearby_demo_wells`, suggested reference и selection contract.
- ✅ второй вызов с `reference_well_id` + `well_ids` возвращает `stage=CROSS_SECTION_READY` и готовый backend-owned `cross_section`.
- ✅ demo selection допускает только `synthetic-correlation-demo-v1`; production well даже в той же точке исключается.
- ✅ invalid/incomplete/duplicate/out-of-discovery selection отклоняется HTTP `422`.
- ✅ demo dataset identifier централизован между runtime workflow и `python -m scripts.seed_correlation_demo`.
- ✅ полный demo HTTP path покрыт реальным PostgreSQL/PostGIS integration test с отдельной production fixture well.
- ✅ README, USER_GUIDE, roadmap и отдельные feature contracts поддерживаются на RU/KK/EN и проверяются documentation CI contract.

## Ближайший P0
1. Хранение/настройка локальных CRS организации; СК-42/Гаусса–Крюгера только по подтверждённому EPSG/WKT/PROJ.
2. Устранить оставшийся SQLAlchemy cartesian-product warning в distance query корреляции без изменения результата PostGIS distance.
3. Controlled vocabularies для lithology/markers/property kinds/units.
4. Добавить normalizer/review для следующего официального ресурса — геологических лицензий — после проверки mapping/license/data quality.
5. Core Dataset manifest/importer.
6. Authentication + AuditLog/revisions для review и изменений master data.
7. Production PySide6 screen для external review на уже стабильном backend view-model contract.
8. Расширить scheduler provider registry на USGS/Macrostrat/OneGeology только после отдельной проверки лицензий и контрактов.

## Релизы
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + первые официальные REST integrations Казахстана + safe oil/gas-field normalization/matching/review — слито в `main`.
- `v0.3`: review UI contract, scheduled external sync/Update All, visual correlation contract, complete synthetic demo workflow и CRS/local settings.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: расширенный matching/review/audit для внешних источников.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пользовательская функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN help/docs, provenance/verification и зелёного CI.
