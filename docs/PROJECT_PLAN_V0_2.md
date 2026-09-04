# GeoKZ — актуальный план развития v0.2+

Статус: `2026-09-04`, ветка `feature/external-review-ui-contract-v0.3`. Фундамент v0.2 слит в `main` после зелёного CI.

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
- ✅ review/matching backend подтверждён зелёными `Python quality checks` и PostgreSQL/PostGIS integration tests на одном head и слит в `main`.
- ✅ UI/view-model contract очереди review: `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view`.
- ✅ view-model возвращает RU/KK/EN title/policy note, `total_pending`, pagination, локализованные candidate names, отдельный `entity_verification_status` и стабильные `matching_status`.
- ✅ action descriptors `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD` содержат `enabled`, `disabled_reason`, `required_fields`, `optional_fields` и точный `path` для PySide6/web.
- ✅ `UNKNOWN` matching status является безопасным forward-compatible fallback для UI.
- ✅ для review view-model добавлены unit tests и реальный PostgreSQL HTTP integration test.
- ✅ источники регистрируются как `AUTOMATIC` с интервалом 168 часов; фактический scheduler ещё не реализован.
- ✅ API key хранится только в `GEOKZ_EGOV_API_KEY`; без ключа локальная база продолжает работать.
- ✅ отдельные RU/KK/EN инструкции: API keys, Kazakhstan Open Data onboarding/naming, field review и review UI contract.
- ✅ README, USER_GUIDE и roadmap поддерживаются на RU/KK/EN + documentation CI contract.

## Ближайший P0
1. Scheduler периодической синхронизации внешних источников + «Обновить всё» с защитой от параллельных запусков и корректным per-source status/error reporting.
2. API/view-model для визуального cross-section viewer: колонки скважин, шкала глубин, реперы, интервалы и линии корреляции.
3. Demo workflow: координата → ближайшие demo-скважины → выбор → корреляционный разрез.
4. Хранение/настройка локальных CRS организации; СК-42/Гаусса–Крюгера только по подтверждённому EPSG/WKT/PROJ.
5. Устранить оставшийся SQLAlchemy cartesian-product warning в distance query корреляции без изменения результата PostGIS distance.
6. Controlled vocabularies для lithology/markers/property kinds/units.
7. Добавить normalizer/review для следующего официального ресурса — геологических лицензий — после проверки mapping/license/data quality.
8. Core Dataset manifest/importer.
9. Authentication + AuditLog/revisions для review и изменений master data.
10. Production PySide6 screen для external review на уже стабильном backend view-model contract.

## Релизы
- `v0.2`: platform/integration/help/spatial/subsurface/correlation foundation + первые официальные REST integrations Казахстана + safe oil/gas-field normalization/matching/review — слито в `main`.
- `v0.3`: review UI contract, visual correlation data contract, CRS/local settings, complete demo workflow и scheduled external sync.
- `v0.4`: PDF/DOCX/LAS/DLIS/WITSML/SEG-Y.
- `v0.5`: расширенный matching/review/audit для внешних источников.
- `v0.6`: unified RU/KK/EN search.
- `v0.7`: GIS/PySide6 + visual correlation viewer.
- `v0.8`: geological model hardening / GeoSciML alignment.
- `v0.9`: AI candidates + human review.
- `v1.0`: production GeoKZ Desktop.

## Definition of Done
Пользовательская функция завершена только при наличии implementation, validation, tests, migration при необходимости, RU/KK/EN help/docs, provenance/verification и зелёного CI.
