# GeoKZ — аутентификация, роли, аудит и история ревизий

Версия контракта: `v0.3`.

## Назначение

GeoKZ разделяет чтение геологической информации и операции, которые изменяют scientific master data или фиксируют экспертное решение. Аутентификация нужна не для скрытия публичных справочных данных, а для того, чтобы каждое изменение имело проверяемого автора, роль, причину и неизменяемую историю.

## Роли

- `editor` — создаёт и редактирует `Source`, `GeologicalEntity` и `Fact`, но не может повышать `verification_status` выше `DRAFT`.
- `expert` — выполняет научную проверку, может переводить master data в `REVIEWED`/`VERIFIED` и принимает решения во внешних review queues.
- `admin` — имеет права expert/editor, управляет локальными учётными записями, устанавливает bundled Core Dataset и читает полный audit log.

Проверка роли выполняется на backend. Клиентский интерфейс не считается доверенной границей безопасности.

## Первый администратор

Первую локальную учётную запись создаёт оператор на машине/сервере GeoKZ. Пароль не передаётся аргументом командной строки и не попадает в shell history:

```text
python -m scripts.auth create-user --username admin --display-name "GeoKZ Administrator" --role admin
```

Команда интерактивно запросит пароль два раза. Минимальная длина пароля — 12 символов. Последующие учётные записи admin создаёт через API.

## Вход и сессия

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

После успешного входа backend возвращает opaque bearer token. Сам token хранится только у клиента; в PostgreSQL сохраняется его SHA-256 hash. Пароли хранятся как salted `scrypt-v1` hash. Срок сессии задаётся:

```env
GEOKZ_AUTH_SESSION_HOURS=12
```

Для защищённых запросов используется заголовок `Authorization: Bearer <token>`. Logout устанавливает `revoked_at`; повторное использование token получает HTTP `401`.

## Управление пользователями

Только `admin`:

```text
POST /api/v1/auth/users
GET  /api/v1/auth/users
```

API никогда не возвращает `password_hash` или hash bearer token.

## Scientific master-data writes

Создание и изменение источников, геологических объектов и фактов требует аутентифицированной сессии:

```text
POST  /api/v1/sources
PATCH /api/v1/sources/{source_id}
POST  /api/v1/entities
PATCH /api/v1/entities/{entity_id}
POST  /api/v1/facts
PATCH /api/v1/facts/{fact_id}
```

PATCH требует `change_reason`. Для каждого успешного CREATE/UPDATE GeoKZ в одной транзакции сохраняет audit record и новый immutable snapshot в `master_data_revisions`. Номер ревизии увеличивается отдельно для каждого ресурса; PostgreSQL advisory transaction lock защищает от гонки при параллельных изменениях.

`editor` может работать с DRAFT, но попытка установить non-DRAFT verification status получает HTTP `403`. `expert` и `admin` могут выполнять научное повышение статуса; это не отменяет evidence/provenance rules.

## Внешний review

Review queues доступны только аутентифицированным пользователям. Решения `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`, а также `ACCEPT/REJECT` административной записи лицензии требуют роли `expert` или `admin`.

Reviewer identity берётся **только из authenticated principal**. Поле `reviewer` в старом request body допускается временно для совместимости, но backend его игнорирует. Поэтому клиент не может подписать решение чужим именем.

Если из внешней записи создаётся новое месторождение, оно остаётся `DRAFT`; в той же транзакции создаётся revision нового `GeologicalEntity` и audit record review-action. Подтверждённый `ExternalEntityLink` по-прежнему не превращает сам геологический объект в `VERIFIED`.

## AuditLog

Полный журнал доступен только admin:

```text
GET /api/v1/audit/logs
```

Поддерживаются фильтры `action`, `resource_type`, `resource_id`, `limit`, `offset`. Audit record содержит snapshot личности исполнителя (`actor_username`, `actor_role`), действие, тип/ID ресурса, причину и технические details.

`audit_logs` и `master_data_revisions` защищены PostgreSQL triggers: обычные `UPDATE` и `DELETE` отклоняются на уровне БД. Это защищает историю даже от ошибки прикладного кода. Удаление user account в будущем не уничтожит actor snapshot: внешний FK может стать NULL, но username/role в audit остаются.

## История ревизий

Любой аутентифицированный пользователь может получить историю scientific master data:

```text
GET /api/v1/audit/revisions/source/{source_id}
GET /api/v1/audit/revisions/geological_entity/{entity_id}
GET /api/v1/audit/revisions/fact/{fact_id}
```

Каждая ревизия содержит `revision_number`, action, полный JSON snapshot после изменения, `change_reason`, actor и timestamp. История не является механизмом автоматического rollback: восстановление старой версии должно быть отдельным явным изменением с новой ревизией, чтобы audit chain не терялся.

## Core Dataset

`GET /api/v1/core-dataset/status` остаётся read-only и доступен без входа. Установка:

```text
POST /api/v1/core-dataset/install
```

требует `admin`. Bundled manifest и checksum validation остаются обязательными. Core Dataset не получает права тихо переписывать user/expert verified master data.

## Безопасность

Не сохраняйте bearer token в Git, issue, screenshot или документацию. Не передавайте пароль через CLI argument. Используйте HTTPS при удалённом доступе. Потерянный token следует отозвать через logout, а при невозможности — завершить/отозвать соответствующую server-side session административным механизмом, когда он будет добавлен.

Этот P0 создаёт локальную auth/RBAC основу. SSO/OIDC, MFA, password reset и централизованная enterprise identity остаются отдельными будущими расширениями и не должны внедряться ценой усложнения локального offline-capable core.
