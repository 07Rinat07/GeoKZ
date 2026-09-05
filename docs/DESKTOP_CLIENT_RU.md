# GeoKZ Desktop — PySide6-клиент

GeoKZ Desktop — Windows/desktop-клиент поверх центрального HTTP API GeoKZ. Клиент **не подключается к PostgreSQL напрямую**, не импортирует SQLAlchemy models и не содержит собственных правил научной верификации. Все решения review, provenance и business rules остаются на backend.

## Установка

Для разработки desktop-компонента установите optional dependency:

```powershell
python -m pip install -e ".[desktop]"
```

Backend запускается отдельно, например на `http://127.0.0.1:8000`.

Запуск:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang ru
```

или:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang ru
```

Поддерживаются `ru`, `kk`, `en`.

## Вход и сессия

Desktop использует:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Opaque bearer token хранится только в памяти процесса. Клиент не записывает пароль или access token в настройки, лог или файл. После закрытия окна выполняется logout и локальное состояние токена очищается.

Роли backend: `editor`, `expert`, `admin`. Клиент отображает текущего пользователя и роль, однако **не считает собственную UI-проверку роли источником истины**. Сервер всегда повторно проверяет полномочия.

## Экран «Источники данных»

Экран агрегирует:

```text
GET /api/v1/system/versions
GET /api/v1/about
GET /api/v1/core-dataset/status
GET /api/v1/integrations/sources
GET /api/v1/integrations/scheduler/status
```

Отображаются:

- версия приложения;
- Alembic/database schema revision;
- bundled Core Dataset version;
- installed Core Dataset version;
- provider/dataset version;
- due/running/error status;
- время последней успешной синхронизации;
- последняя ошибка источника.

Кнопка «Обновить всё» вызывает `POST /api/v1/integrations/sync-all`. Внешняя синхронизация обновляет RAW/staging и sync history, но не подтверждает геологические факты и не превращает DRAFT/REVIEW_REQUIRED данные в VERIFIED.

## Проверка нефтегазовых месторождений

Очередь строится только по backend-owned contract:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

Клиент показывает `raw_payload`, `normalized_payload`, matching status, кандидатов и `entity_verification_status`.

Главное правило: `ExternalEntityLink=VERIFIED` означает проверенную связь с официальной external record, но **не означает `GeologicalEntity=VERIFIED`**.

Доступные действия приходят с сервера в action descriptors:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Desktop не хранит таблицу business rules. Он читает `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method` и `path`. Если action disabled, UI не выполняет его. Сервер всё равно является окончательным authority.

Поле `reviewer` desktop не отправляет. Reviewer identity определяется authenticated session на сервере, поэтому подменить автора решения строкой из UI нельзя.

## Проверка лицензий

Административная очередь лицензий:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Решения:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` означает только экспертную проверку нормализованной административной записи относительно RAW/upstream payload. Это не создаёт `ExternalEntityLink`, не создаёт `GeologicalEntity` и не публикует геологический факт.

## Provenance и аудит

В review-экранах рядом показываются RAW и normalized payload. Это позволяет видеть исходное значение поставщика и внутреннее представление GeoKZ одновременно.

Для истории master data desktop использует:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

Полный `AuditLog` доступен `admin`. Revision history доступна authenticated пользователям для поддерживаемых resource types `source`, `geological_entity`, `fact`.

Audit/revision history append-only на уровне PostgreSQL. Desktop не имеет API для её перезаписи или удаления.

## Асинхронность UI

HTTP-запросы выполняются через `QThreadPool/QRunnable`, а не блокируют Qt event loop. Ошибки сети и HTTP API переводятся в явные сообщения пользователю. При ошибке одного запроса клиент не изменяет научные данные локально и не пытается «угадать» успешный результат.

## Архитектурные границы

```text
PySide6 widgets
    ↓
GeoKZApiClient (httpx)
    ↓ HTTPS/HTTP
FastAPI application/use cases
    ↓
domain + repositories
    ↓
PostgreSQL/PostGIS
```

Запрещённый путь:

```text
PySide6 → SQLAlchemy model → PostgreSQL
```

Такое прямое подключение нарушило бы RBAC, AuditLog, revision history и backend-owned review contract.

## Тестирование

Unit tests desktop API client проверяют:

- bearer token добавляется только после login;
- token остаётся в памяти клиента;
- disabled action не отправляется;
- обязательные поля action descriptor валидируются до HTTP запроса;
- server-owned field-review path используется без локальной реконструкции;
- RU/KK/EN desktop localization имеет одинаковый набор ключей;
- HTTP `detail` не теряется при отображении ошибки.

PostgreSQL/PostGIS integration test для `GET /api/v1/system/versions` проверяет фактический Alembic head и Core Dataset metadata.

## Текущие ограничения

Первый production-oriented desktop slice пока не включает полноценные карты, cross-section renderer, offline cache и Windows installer. Он формирует безопасный каркас login/session, Data Sources, external review и provenance. Следующие desktop-срезы могут добавлять Territory Explorer, Well Passport и корреляционный viewer, продолжая использовать HTTP API и backend-owned contracts.
