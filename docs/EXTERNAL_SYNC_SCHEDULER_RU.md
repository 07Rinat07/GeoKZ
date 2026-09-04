# GeoKZ — scheduler внешней синхронизации (RU)

## Назначение

GeoKZ синхронизирует разрешённые внешние источники отдельно от основной FastAPI обработки. Периодический scheduler запущен как отдельный процесс/контейнер и не создаёт background loop внутри каждого API worker. Это предотвращает дублирующие загрузки при масштабировании API.

Основной принцип:

```text
GeoKZ API / PySide6
        |
        +--> POST /api/v1/integrations/sync-all       # ручное «Обновить всё»
        |
        +--> GET  /api/v1/integrations/scheduler/status

Dedicated scheduler process
        |
        +--> ExternalSyncCoordinator.sync_due()
        |
        +--> source reservation in PostgreSQL
        |
        +--> connector -> RAW/staging -> checksum/diff
```

## Режимы запуска

### Ручное «Обновить всё»

```text
POST /api/v1/integrations/sync-all
```

Команда пытается синхронизировать все включённые источники, для которых GeoKZ знает connector. Источники с `enabled=false` пропускаются. Если конкретный источник уже синхронизируется, весь batch не падает: для него возвращается `ALREADY_RUNNING`, а остальные источники продолжают обрабатываться.

### Плановый запуск только просроченных источников

```text
POST /api/v1/integrations/scheduler/run-due
```

Этот endpoint используется для диагностики и ручного запуска того же алгоритма, что выполняет отдельный scheduler process. Для production не нужно вызывать его из нескольких cron/FastAPI worker одновременно.

Scheduler проверяет только источники `sync_mode=AUTOMATIC`. Для каждого источника используется его `sync_interval_hours`.

### Состояние scheduler

```text
GET /api/v1/integrations/scheduler/status
```

Ответ содержит:

- `poll_seconds` — частота проверки отдельным scheduler process;
- `failure_retry_hours` — интервал повторной попытки после последней ошибки;
- `running_timeout_hours` — порог stale `RUNNING`;
- `sources[]` — состояние каждого источника;
- `next_due_at` и `due`;
- `running_run_id`, если активный sync уже выполняется;
- последнюю успешную синхронизацию и последнюю ошибку.

## Защита от параллельных запусков

Перед созданием нового `ExternalSyncRun(status=RUNNING)` GeoKZ кратковременно блокирует строку `external_data_sources` через PostgreSQL `SELECT ... FOR UPDATE`.

Критическая секция включает только резервирование run:

1. блокировка source row;
2. поиск актуального `RUNNING`;
3. перевод слишком старых `RUNNING` в `FAILED`;
4. создание нового `RUNNING`;
5. commit и освобождение row lock.

Внешний HTTP transfer выполняется уже без удержания row lock. Поэтому медленный внешний API не блокирует чтение статуса и другие источники.

Если второй запрос приходит во время активного run, он получает `ExternalSyncAlreadyRunningError`, а REST endpoint синхронизации одного источника преобразует это в HTTP `409`.

## Stale RUNNING recovery

Если процесс аварийно завершился после создания `RUNNING`, запись может остаться незакрытой. GeoKZ не считает такой run вечной блокировкой.

Порог задаётся:

```env
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

При следующем резервировании run старые `RUNNING`, у которых `started_at` старше порога, переводятся в `FAILED` с диагностическим `error_message`. После этого новый run может стартовать.

## Политика due/retry

Для нового `AUTOMATIC` источника без истории синхронизации `due=true` сразу.

После успеха:

```text
next_due_at = last_success_at + sync_interval_hours
```

Если последняя попытка завершилась ошибкой позже последнего успеха:

```text
next_due_at = last_error_at + min(sync_interval_hours, failure_retry_hours)
```

То есть retry не может быть реже обычного интервала источника.

Источники `MANUAL` и отключённые источники не имеют планового `next_due_at`.

## Batch status

`sync-all` и `run-due` возвращают общий summary и результат по каждому source.

Основные `dispatch_status`:

- `SUCCESS` — run успешно завершён;
- `FAILED` — connector/config/provider завершился ошибкой;
- `ALREADY_RUNNING` — источник уже занят другим run;
- `SKIPPED_NOT_DUE` — плановый batch: срок ещё не наступил;
- `SKIPPED_DISABLED` — источник отключён;
- `SKIPPED_MANUAL` — источник не участвует в scheduled due;
- `SKIPPED_UNSUPPORTED` — source зарегистрирован, но connector factory ещё не реализован.

Ошибка одного источника не отменяет обработку остальных источников batch.

## Docker Compose

`docker compose up --build` запускает три процесса:

```text
geokz-db
geokz-api
geokz-external-sync-scheduler
```

Scheduler ждёт healthy API, затем запускается командой:

```text
python -m scripts.external_sync_scheduler
```

Однократная диагностическая проверка:

```text
python -m scripts.external_sync_scheduler --once
```

## Настройки

`.env`:

```env
GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS=300
GEOKZ_EXTERNAL_SYNC_FAILURE_RETRY_HOURS=6
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

`poll_seconds` не меняет `sync_interval_hours` источника. Он только определяет, как часто worker проверяет, не наступил ли `next_due_at`.

## API key и offline behavior

Scheduler не делает внешние API обязательной runtime-зависимостью GeoKZ. Если `GEOKZ_EGOV_API_KEY` отсутствует, локальная БД, поиск, паспорта и review продолжают работать. Попытка eGov sync фиксируется как per-source error, но scheduler process остаётся жив.

Нельзя передавать API key в REST payload, URL GeoKZ, UI storage или Git. Ключ читается только из настроенной среды выполнения.

## Границы ответственности

Scheduler отвечает только за безопасное получение RAW/staging записей и историю sync run. Он не подтверждает geological facts и не публикует изменения master data.

После sync применяются отдельные шаги normalization -> matching -> human review. Verified GeoKZ facts не перезаписываются scheduler-ом автоматически.
