# GeoKZ — Documentation Policy / Құжаттама саясаты / Политика документации

Documentation is part of Definition of Done. Пайдаланушыға арналған функция және пользовательская функция считается завершённой только вместе с актуальной документацией RU/KK/EN и CI contract.

## Обязательный общий набор / Міндетті жалпы жинақ / Required common set

Каждый user-facing feature slice обновляет при необходимости:

- `README.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`;
- `docs/PROJECT_PLAN_V0_2_EN.md`.

## Feature-specific contracts

При изменении соответствующей области обновляются все три языковые версии:

- Core Dataset: `docs/CORE_DATASET_RU.md`, `docs/CORE_DATASET_KK.md`, `docs/CORE_DATASET_EN.md`;
- external API secrets: `docs/EXTERNAL_API_KEYS_RU.md`, `docs/EXTERNAL_API_KEYS_KK.md`, `docs/EXTERNAL_API_KEYS_EN.md`;
- Kazakhstan Open Data: `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`;
- oil/gas field review: `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`;
- geological-study-license review: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md`, `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_KK.md`, `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_EN.md`;
- backend review view-model: `docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md`;
- external scheduler/Update All: `docs/EXTERNAL_SYNC_SCHEDULER_RU.md`, `docs/EXTERNAL_SYNC_SCHEDULER_KK.md`, `docs/EXTERNAL_SYNC_SCHEDULER_EN.md`;
- visual correlation: `docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`, `docs/CROSS_SECTION_VIEW_CONTRACT_KK.md`, `docs/CROSS_SECTION_VIEW_CONTRACT_EN.md`;
- synthetic demo workflow: `docs/DEMO_CORRELATION_WORKFLOW_RU.md`, `docs/DEMO_CORRELATION_WORKFLOW_KK.md`, `docs/DEMO_CORRELATION_WORKFLOW_EN.md`;
- authentication/RBAC/audit/revisions: `docs/AUTH_AUDIT_REVISIONS_RU.md`, `docs/AUTH_AUDIT_REVISIONS_KK.md`, `docs/AUTH_AUDIT_REVISIONS_EN.md`;
- PySide6 desktop client: `docs/DESKTOP_CLIENT_RU.md`, `docs/DESKTOP_CLIENT_KK.md`, `docs/DESKTOP_CLIENT_EN.md`.

## Непереговорные инварианты / Міндетті invariants / Non-negotiable invariants

1. **Evidence-first.** RAW/source wording и provenance не уничтожаются нормализацией.
2. **Human-in-the-loop.** External API/AI не повышают scientific verification status автоматически.
3. **Link verification ≠ entity verification.** `ExternalEntityLink=VERIFIED` не делает `GeologicalEntity=VERIFIED`; external-derived entity создаётся как `DRAFT`.
4. **License record review.** `ACCEPTED` для административной лицензии не создаёт `ExternalEntityLink`, `GeologicalEntity` или geological fact.
5. **Depth safety.** TVDSS/TVD/MD не смешиваются молча; incompatible data не соединяются correlation line.
6. **CRS safety.** Projected X/Y требует подтверждённой CRS/axis order; CRS не угадывается по числам.
7. **Synthetic isolation.** Demo wells не смешиваются с production wells.
8. **Scheduler isolation.** Periodic scheduler работает отдельным process/service, а не background loop в каждом FastAPI worker.
9. **Independent versions.** Application version, Alembic schema revision, Core Dataset version/schema и provider versions документируются отдельно.
10. **Authentication boundary.** Reviewer identity берётся из authenticated session; client-supplied reviewer string не является authority.
11. **Append-only history.** AuditLog/revisions не перезаписываются и не удаляются обычными application paths.
12. **Desktop HTTP boundary.** PySide6 не импортирует SQLAlchemy models и не подключается к PostgreSQL напрямую.
13. **Backend-owned actions.** Desktop/UI исполняет server action descriptors (`enabled`, `required_fields`, `method`, `path`) и не дублирует review business rules.
14. **Secret safety.** Реальные API keys, passwords и bearer tokens запрещено включать в Git, docs, issues, PRs, screenshots или examples.
15. **RU/KK/EN parity.** Пользовательская функция не complete, если инструкция/подсказка отсутствует хотя бы на одном из трёх языков.

## Core Dataset rules

Документация Core Dataset обязана явно описывать:

- bundled и installed version;
- `schema_version`;
- manifest SHA-256;
- `geokz-core:` namespace;
- compatibility gate;
- transactional install/rollback;
- idempotence (`changed=false`);
- отсутствие вымышленных production geological facts в bootstrap.

## Desktop rules

Desktop documentation обязана содержать:

```text
POST /api/v1/auth/login
GET  /api/v1/system/versions
POST /api/v1/integrations/sync-all
GET  /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
GET  /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
GET  /api/v1/audit/logs
GET  /api/v1/audit/revisions/{resource_type}/{resource_id}
```

и объяснять, что bearer token хранится только в памяти процесса, HTTP work не блокирует Qt event loop, а desktop не является security authority поверх backend RBAC.

## CI contract

`tests/test_documentation_contract.py` проверяет наличие и ключевые инварианты документации. Если API contract, version semantics, review semantics, desktop boundary или security policy меняются, CI contract обновляется в том же feature slice.

## Definition of Done

```text
feature branch
→ code/contracts/migrations
→ unit tests
→ PostgreSQL/PostGIS integration
→ README + USER_GUIDE RU/KK/EN
→ roadmap RU/KK/EN
→ dedicated docs RU/KK/EN
→ exact-head CI green
→ PR
→ PR-CI green on the same SHA
→ squash merge main
```

Автор / Автор / Author: **Sarmuldin Rinat — ura07srr@gmail.com**.
