# GeoKZ — канал обновления Core Dataset (RU)

Версия контракта: `v0.3`.

## Назначение

GeoKZ Core Dataset обновляется независимо от версии приложения и схемы БД. Онлайн-канал предназначен только для доверенных, подписанных snapshot-пакетов GeoKZ и не является механизмом произвольного импорта файлов с рабочего компьютера. Локальная работа GeoKZ не зависит от доступности update-сервера: если канал не настроен, встроенный Core Dataset и вся локальная БД продолжают работать.

Административные endpoints:

```text
GET  /api/v1/core-dataset/update/status
POST /api/v1/core-dataset/update/apply?dry_run=true&lang=ru
POST /api/v1/core-dataset/update/apply?lang=ru
POST /api/v1/core-dataset/update/rollback?lang=ru
```

Все три операции update/rollback требуют роли `admin`. Проверка обычного встроенного набора остаётся отдельной через `/api/v1/core-dataset/status`.

## Модель доверия

Update descriptor — JSON-документ схемы `channel_schema_version=1`. Он содержит `dataset_code`, `dataset_version`, `core_dataset_schema_version`, SHA-256 manifest, HTTPS URL архива, SHA-256 самого ZIP, дату публикации, ограничения совместимости, `key_id` и `signature`.

Подпись проверяется Ed25519. GeoKZ хранит только доверенные **публичные** ключи. Приватный signing key не должен находиться в `.env`, репозитории, desktop-клиенте или БД приложения.

Конфигурация:

```env
GEOKZ_CORE_DATASET_UPDATE_MANIFEST_URL=https://updates.example/geokz/core/channel.json
GEOKZ_CORE_DATASET_UPDATE_TRUSTED_PUBLIC_KEYS={"prod-2026":"<base64-raw-ed25519-public-key>"}
GEOKZ_CORE_DATASET_UPDATE_CACHE_DIR=data/runtime/core_dataset_updates
GEOKZ_CORE_DATASET_UPDATE_MAX_BYTES=134217728
```

Если URL или trusted-key map отсутствуют, статус канала — `DISABLED`. Descriptor URL и `bundle_url` должны использовать HTTPS. HTTP redirects намеренно не следуются: смена origin не должна происходить незаметно.

## Проверка перед установкой

Последовательность намеренно fail-closed:

1. загрузить descriptor;
2. проверить известный `key_id` и Ed25519 signature по canonical JSON без поля `signature`;
3. проверить совместимость;
4. скачать ZIP с ограничением размера;
5. проверить SHA-256 ZIP против подписанного descriptor;
6. извлечь в staging/cache с защитой от path traversal, absolute path и symlink;
7. проверить `manifest.json` существующим Core Dataset validator;
8. проверить SHA-256 manifest, `dataset_code`, `dataset_version`, `schema_version` против подписанного descriptor;
9. только после этого перейти к transactional activation.

При любой ошибке signature/checksum/manifest/compatibility master data не меняются.

## Compatibility gate

Поддерживаются три независимые оси совместимости:

- приложение: `minimum_app_version` сравнивается с `PROJECT_VERSION`;
- схема БД: `required_database_revision` должна совпадать с текущим `alembic_version`;
- формат Core Dataset: `core_dataset_schema_version` должен совпадать с поддерживаемым `CORE_DATASET_SCHEMA_VERSION`.

Текущая миграция state-модели update channel — `20260905_0011`. Онлайн-обновление также требует сначала установить bundled baseline `geokz-core`; сеть не заменяет bootstrap.

Статус `/api/v1/core-dataset/update/status` возвращает одно из состояний:

- `DISABLED` — канал не настроен;
- `FAILED` — descriptor нельзя безопасно получить или проверить;
- `CURRENT` — установленный manifest совпадает с подписанным release;
- `AVAILABLE` — доступен совместимый новый release;
- `INCOMPATIBLE` — release подписан, но требует другую версию приложения/БД/Core Dataset schema.

Ответ отдельно показывает `signature_verified`, `compatible`, `compatibility_issues`, available/installed version и возможность rollback.

## Transactional activation

Перед записью можно выполнить `dry_run=true`. В этом режиме проходит signature/checksum/ZIP/manifest validation и существующая Core Dataset validation, но состояние БД не активируется.

При реальной установке GeoKZ сначала готовит и проверяет пакет, затем берёт PostgreSQL advisory transaction lock и row lock `CoreDatasetState`. После блокировки состояние перечитывается. Если другой процесс успел изменить установленный manifest во время подготовки, операция прекращается с conflict и должна быть повторена. Так network I/O не выполняется под row lock.

Перед переключением сохраняются metadata предыдущего snapshot: версия, schema, manifest SHA-256, source path, checksums и item counts. Затем в той же транзакции Core Dataset importer выполняет upsert и обновляет `CoreDatasetState`.

AuditLog получает authenticated actor, reason `signed_online_update`, исходную/целевую версии, manifest SHA-256, bundle SHA-256, `key_id` и descriptor URL. Пользователь не может передать чужое имя вместо authenticated principal.

## Rollback

GeoKZ поддерживает один безопасный предыдущий snapshot. Endpoint:

```text
POST /api/v1/core-dataset/update/rollback?lang=ru
```

не является «удалить всё, что появилось в новой версии». Текущий Core Dataset importer по архитектуре upsert-only, потому что удаление записей может затронуть master data, дополненные пользователем или экспертом.

Поэтому rollback разрешается только если current и previous bundle содержат одинаковые множества `external_id` отдельно для sources, regions, entities и facts. Если новая версия добавила или убрала identity, операция блокируется. GeoKZ не делает hard delete ради отката.

Перед rollback повторно проверяются оба локальных manifest, SHA-256 предыдущего manifest и identity sets. После подготовки берутся advisory/row locks и ещё раз проверяется, что state не изменился конкурентным процессом. Успешная операция фиксируется в AuditLog с reason `safe_rollback`.

Если cache-файл предыдущего snapshot отсутствует или checksum не совпадает, rollback запрещается как unverifiable.

## Безопасность и эксплуатация

Update server не получает доступ к локальной БД. Desktop PySide6 обращается только к HTTPS API GeoKZ, а не загружает update-файлы напрямую в PostgreSQL. Signing private key должен храниться отдельно от runtime GeoKZ. При ротации ключей новый public key добавляется под новым `key_id`; старый удаляется из trust store только после окончания периода поддержки соответствующих release descriptor.

Не следует автоматически устанавливать `AVAILABLE` release без административного решения. UI должен показывать `CURRENT`, `AVAILABLE`, `INCOMPATIBLE`, `FAILED`, подписавший `key_id`, compatibility issues и наличие rollback. Ошибка online update не должна блокировать просмотр ранее установленных геологических данных.

## Инварианты данных

Core Dataset update не отменяет общие правила GeoKZ:

- проверенные внешние ссылки не делают `GeologicalEntity=VERIFIED` автоматически;
- update не должен тихо удалять master data;
- provenance и evidence сохраняются;
- внешняя сеть является необязательным enrichment/update-слоем;
- PostgreSQL/PostGIS остаётся источником текущего локального состояния;
- история install/update/rollback должна быть аудируемой и привязанной к authenticated admin.
