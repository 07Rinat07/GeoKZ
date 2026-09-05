# GeoKZ — руководство пользователя (RU)

Версия: `0.3-dev`.

GeoKZ — evidence-based геологическая информационная система Казахстана. Основной путь: территория или координата → месторождения, структуры, скважины и сейсмика → паспорта → интервалы/ГИС/керн/испытания → корреляция → первичные источники, provenance и экспертная проверка.

## Главное правило данных

Внешний API, импорт или ИИ не переписывает verified master data автоматически. GeoKZ сохраняет RAW/source wording, нормализованные значения, источник, версию, checksum и review status. Подтверждение связи с внешней записью не означает автоматическую верификацию самого геологического объекта.

## Языки

Пользовательский интерфейс и документация поддерживаются на русском, казахском и английском: `ru`, `kk`, `en`.

## Поиск по координатам и CRS

GeoKZ принимает WGS84 latitude/longitude и projected X/Y. Для projected coordinates пользователь обязан указать подтверждённую CRS и порядок осей. Большие X/Y не используются для угадывания системы координат. Поддерживаются WGS84, UTM 38N–45N и persistent organization-local CRS через EPSG/WKT/PROJ.

Поиск ближайших объектов выполняется PostGIS в метрах. Результат может включать геологические объекты, месторождения, скважины, интервалы и сейсмику.

## Паспорт скважины и корреляция

Well Passport объединяет координаты, trajectory MD/TVD/TVDSS, стратиграфию, литологию, коллекторы, флюиды, porosity/permeability, logs, tests, core и seismic links.

Корреляция соседних скважин:

```text
POST /api/v1/correlation/wells/view
```

Backend выбирает совместимую depth reference `TVDSS → TVD → MD`. Несовместимые глубины не соединяются автоматически.

Synthetic end-to-end workflow:

```text
POST /api/v1/correlation/demo/workflow
```

Demo wells помечены как synthetic и не смешиваются с production data.

## GeoKZ Core Dataset

Bundled baseline версионируется независимо от приложения и Alembic.

```text
GET  /api/v1/core-dataset/status
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
POST /api/v1/core-dataset/install?lang=ru
```

Текущий bundled snapshot: `2026.09.0-bootstrap`, `schema_version=1`. Перед установкой проверяются manifest schema, SHA-256, path traversal, namespace `geokz-core:`, duplicate IDs и ссылки. Установка transactional; повтор той же версии возвращает `changed=false`.

## Внешние источники и синхронизация

Сейчас встроены Kazakhstan Open Data datasets:

- `kz-egov-oil-gas-fields` → `stat_kgn_117/v10`;
- `kz-egov-geological-study-licenses` → `zher_koinauyn_geologiyalyk_zer2/v6`.

Ручное обновление всех источников:

```text
POST /api/v1/integrations/sync-all
```

Состояние scheduler:

```text
GET  /api/v1/integrations/scheduler/status
POST /api/v1/integrations/scheduler/run-due
```

Scheduler работает отдельным process/service, не внутри каждого FastAPI worker. Параллельный `RUNNING` защищается PostgreSQL locking.

## Нефтегазовые месторождения: normalize → match → review

После RAW sync:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

Техническая очередь:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

UI-owned view contract:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=ru&limit=100&offset=0
```

Backend отдаёт `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method`, `path` для `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`. Клиент не дублирует эти business rules.

`ExternalEntityLink=VERIFIED` подтверждает связь с официальной записью, но не делает `GeologicalEntity=VERIFIED`. Новый объект из `UNMATCHED` создаётся только как `DRAFT`.

## Лицензии на геологическое изучение недр

Нормализация административного реестра:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Очередь:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

`ACCEPTED` означает только review normalized administrative record относительно RAW upstream payload. Это не создаёт `ExternalEntityLink`, `GeologicalEntity` или geological fact.

## Аутентификация, роли и аудит

Вход:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Роли: `editor`, `expert`, `admin`. Scientific review decision выполняет `expert/admin`; `admin` также управляет пользователями и читает полный audit log.

Reviewer identity определяется authenticated session на сервере, а не строкой `reviewer` от клиента.

История:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

AuditLog и revisions защищены append-only правилами PostgreSQL.

## Production PySide6 Desktop

Desktop-клиент использует только HTTP API и не импортирует SQLAlchemy models.

Установка:

```powershell
python -m pip install -e ".[desktop]"
```

Запуск:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang ru
```

или:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang ru
```

Экран «Источники данных» получает независимые версии через:

```text
GET /api/v1/system/versions
```

и показывает Application version, database/Alembic schema revision, bundled/installed Core Dataset, provider versions, due/running/error status и last success/error.

Desktop включает:

- login/logout с bearer token только в памяти процесса;
- «Источники данных» + «Обновить всё»;
- field review по server-owned action descriptors;
- license ACCEPT/REJECT;
- RAW/normalized provenance;
- AuditLog/revision viewer;
- контекстные подсказки RU/KK/EN;
- HTTP work через `QThreadPool/QRunnable`, чтобы не блокировать Qt event loop.

Подробно: `docs/DESKTOP_CLIENT_RU.md` и `docs/AUTH_AUDIT_REVISIONS_RU.md`.

## API key data.egov.kz

Для реального API v4 download нужен developer API key. Он хранится только локально:

```env
GEOKZ_EGOV_API_KEY=ВАШ_РЕАЛЬНЫЙ_КЛЮЧ
```

Ключ нельзя коммитить, публиковать в issue/PR, документации или скриншотах. GeoKZ core работает и без него.

## Автор

**Sarmuldin Rinat — ura07srr@gmail.com**
