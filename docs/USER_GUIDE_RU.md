# GeoKZ — руководство пользователя (RU)

Версия: `0.3-dev`.

## Назначение
GeoKZ объединяет геологическую информацию по территории, месторождению, структуре и скважине из собственной базы и разрешённых внешних источников.

Основной путь: территория или координата → месторождения/структуры/скважины/сейсмика → паспорт объекта → паспорт скважины → интервалы, литология, ГИС, керн, испытания, нефть/газ/вода → корреляция соседних скважин → источник и доказательство.

## Языки
Интерфейс, справочники, названия, подсказки и пользовательская документация поддерживаются на русском, казахском и английском.

## Поиск по координатам
Географический ввод: `43.652341 / 51.168420`. Запятая также принимается.

Проекционный ввод: `X=5085125.325`, `Y=711157.665`. Также принимается `5085125,325 / 711157,665`.

Для больших X/Y необходимо указать исходную систему координат: EPSG, UTM-зону, СК-42/Гаусса–Крюгера либо настроенную локальную CRS. Также указывается порядок осей: X=Easting/Y=Northing или X=Northing/Y=Easting. GeoKZ не угадывает CRS только по числам.

CRS-помощник предлагает WGS84 и UTM-зоны 38N–45N, покрывающие диапазон долгот Казахстана. Подсказка по долготе помогает сузить выбор, но не подтверждает систему исходного документа. СК-42/Гаусса–Крюгера и локальная система предприятия должны задаваться по подтверждённому EPSG/WKT/PROJ-описанию.

После ввода GeoKZ преобразует рабочую точку в WGS84 и выполняет поиск в выбранном радиусе. Результат содержит административный контекст, ближайшие месторождения/геологические объекты, пробурённые скважины с расстоянием и интервалами, а также сейсмические исследования. По найденной скважине можно открыть полный паспорт.

## Паспорт скважины
Содержит координаты, тип/оператора/статус, даты, глубину, траекторию MD/TVD/TVDSS, интервалы, стратиграфию, литологию, нефть/газ/воду, пористость/проницаемость, ГИС/каротаж, испытания, дебиты, давление/температуру, керн/образцы и связанные документы.

## Корреляция разрезов соседних скважин
После координатного поиска пользователь отмечает нужные скважины, назначает одну опорной и запускает сопоставление. GeoKZ сравнивает реперы, литологию, коллекторы, нефть/газ/воду, глубины, мощности, net pay, пористость и проницаемость визуально и текстом.

Для сопоставления предпочтительно используется TVDSS. Несовместимые системы глубин не соединяются автоматической линией. Каждая корреляционная отметка должна иметь источник, метод интерпретации и статус проверки.

Демонстрационный набор GeoKZ содержит только явно маркированные synthetic/demo скважины и предназначен для проверки интерфейса; он не является производственной геологической информацией.

## GeoKZ Core Dataset

GeoKZ поставляет независимо версионируемый базовый набор данных. Его версия не равна версии приложения и не равна Alembic revision.

Текущий bundled snapshot:

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
```

Проверить, какая версия вложена в приложение и какая установлена в текущую БД:

```text
GET /api/v1/core-dataset/status
```

`update_available=true` означает, что bundled manifest отличается от установленного состояния или Core Dataset ещё не установлен.

Перед записью можно выполнить dry-run:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
```

Установить bundled snapshot:

```text
POST /api/v1/core-dataset/install?lang=ru
```

Перед изменением БД GeoKZ проверяет manifest schema, `schema_version`, required files, SHA-256, защиту от path traversal, типы payload, duplicate `external_id`, namespace `geokz-core:` и внутренние ссылки. Все upsert-операции выполняются одной транзакцией. При ошибке происходит rollback; состояние установки фиксируется только после полного успеха.

Повторная установка того же manifest идемпотентна и возвращает `changed=false`.

Первый bootstrap намеренно минимален: содержит внутреннюю metadata-запись и country-level запись «Республика Казахстан» без утверждения boundary geometry. Геологические `entities` и `facts` не добавляются без доказуемых источников.

Для администратора доступны CLI-команды:

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Подробно: `docs/CORE_DATASET_RU.md`.

## Источники и обновление
Внешние данные не перезаписывают проверенные значения автоматически. GeoKZ хранит полученные записи в RAW/staging-слое, после чего они могут проходить нормализацию, сопоставление с объектами GeoKZ и экспертную проверку.

В текущей версии подключён официальный портал открытых данных Казахстана `data.egov.kz` через API v4. Зарегистрированы два геологических набора:

1. `kz-egov-oil-gas-fields` — перечень нефтегазовых месторождений Республики Казахстан (`apiUri=stat_kgn_117`, версия `v10`).
2. `kz-egov-geological-study-licenses` — реестр лицензий на геологическое изучение недр (`apiUri=zher_koinauyn_geologiyalyk_zer2`, версия `v6`).

GeoKZ сохраняет официальные `apiUri` и `version` отдельно. Перед подключением или обновлением ресурса схема полей проверяется через metadata и mapping портала. Технические имена RAW-полей не переименовываются; нормализованные поля GeoKZ создаются отдельно.

Источники регистрируются с автоматическим интервалом обновления 168 часов (раз в неделю), при этом ручное обновление доступно в любое время.

### «Обновить всё» и плановая синхронизация

Для ручного обновления всех включённых источников используется:

```text
POST /api/v1/integrations/sync-all
```

GeoKZ возвращает общий batch summary и отдельный результат для каждого source. Ошибка одного provider не отменяет остальные обновления. Возможны `SUCCESS`, `FAILED`, `ALREADY_RUNNING`, `SKIPPED_DISABLED` и `SKIPPED_UNSUPPORTED`.

Состояние периодической синхронизации:

```text
GET /api/v1/integrations/scheduler/status
```

Поля `next_due_at`, `due` и `running_run_id` позволяют будущему PySide6 UI показать, когда источник будет проверен снова и выполняется ли обновление сейчас.

Отдельный scheduler process выполняет только просроченные `AUTOMATIC` источники:

```text
POST /api/v1/integrations/scheduler/run-due
```

В Docker он запускается как `geokz-external-sync-scheduler`; background loop внутри FastAPI workers не используется. PostgreSQL row lock защищает источник от двух параллельных `RUNNING` run. Слишком старый `RUNNING` после configurable timeout переводится в `FAILED`, после чего источник можно синхронизировать снова.

После синхронизации `kz-egov-oil-gas-fields` можно запустить обработку `process`. GeoKZ извлекает название месторождения и ищет совпадение среди уже существующих месторождений и их алиасов. Совпадение не считается подтверждённым автоматически: создаётся кандидат со статусом `REVIEW_REQUIRED`. Неоднозначные и ненайденные записи остаются для последующей экспертной проверки.

## Экспертная проверка месторождений из внешнего источника
Техническая очередь кандидатов доступна через:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Для пользовательского интерфейса добавлена отдельная локализованная view-model:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=ru&limit=100&offset=0
```

Она возвращает общее число pending-записей, пагинацию, отображаемые названия, кандидатов, `entity_verification_status` и готовые action descriptors (`CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`). UI получает `enabled`, `disabled_reason`, `required_fields`, `optional_fields` и точный `path`, поэтому не должен повторять бизнес-правила backend.

Для записи можно выполнить одно из явных действий:

- подтвердить предложенную связь с существующим месторождением;
- отклонить кандидата с обязательным комментарием;
- вручную связать запись с другим существующим `GeologicalEntity(object_type="field")`;
- создать новое месторождение только из `matching.status=UNMATCHED`.

Подтверждение связи переводит `ExternalEntityLink` в `VERIFIED`, но **не меняет автоматически `verification_status` самого `GeologicalEntity`**. Если создаётся новый объект, он всегда создаётся как `DRAFT` и должен отдельно пройти геологическую проверку по источникам, координатам, скважинам, стратиграфии и другим данным.

Основные действия API:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

Повторный `process` не должен молча изменять reviewer-locked решения (`VERIFIED`, `REJECTED`, `MANUAL`, `verified_by` или review comment).

## Экспертная проверка реестра лицензий на геологическое изучение недр

Для `kz-egov-geological-study-licenses` используется другой, record-level workflow. Официальная карточка `v6` содержит административные сведения о лицензии, но не даёт проверяемого стабильного идентификатора месторождения/геологического объекта и geometry, поэтому GeoKZ не создаёт `ExternalEntityLink` автоматически.

После RAW-sync выполните:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

Normalizer сохраняет исходный `raw_payload` и отдельно извлекает номер/дату лицензии, вид, срок, основание, issuing authority, holder и БИН. Запись получает `REVIEW_REQUIRED`, а `review.entity_matching=NOT_APPLICABLE`.

Очередь:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Решения:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` означает только, что административная normalized-запись проверена относительно upstream payload. Это не создаёт `GeologicalEntity`, не подтверждает геологические данные и не повышает `VerificationStatus`. Если upstream checksum изменился, прежние `reviewed_by`, `reviewed_at`, `review_comment` сбрасываются и требуется новая проверка.

Подробно: `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md`.

## REST API GeoKZ

- `GET /api/v1/about` — сведения о приложении и bundled Core Dataset version;
- `GET /api/v1/core-dataset/status` — bundled/installed Core Dataset state и `update_available`;
- `POST /api/v1/core-dataset/install` — dry-run или транзакционная установка bundled Core Dataset;
- `GET /api/v1/integrations/sources` — зарегистрированные внешние источники и последнее состояние;
- `GET /api/v1/integrations/scheduler/status` — due/running/error состояние scheduler;
- `POST /api/v1/integrations/sync-all` — ручное «Обновить всё»;
- `POST /api/v1/integrations/scheduler/run-due` — выполнить scheduled due алгоритм один раз;
- `GET /api/v1/integrations/kazakhstan/catalog` — показать доступные официальные ресурсы, их `api_uri`, версию и endpoint-ы;
- `GET /api/v1/integrations/kazakhstan/{code}/schema` — получить официальные metadata и mapping ресурса до импорта;
- `POST /api/v1/integrations/kazakhstan/register` — зарегистрировать их в локальной БД GeoKZ;
- `POST /api/v1/integrations/kazakhstan/{code}/sync` — выполнить ручную синхронизацию выбранного ресурса;
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — нормализовать и сопоставить RAW-записи месторождений с объектами GeoKZ, не публикуя совпадения автоматически;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review` — показать техническую очередь экспертной проверки;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` — получить локализованный UI/view-model contract очереди review;
- `POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process` — нормализовать RAW-записи лицензий без автоматического entity matching;
- `GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records` — очередь record-level review лицензий.

Для загрузки данных портал требует API-ключ разработчика. Ключ задаётся только через переменную окружения `GEOKZ_EGOV_API_KEY` и не должен сохраняться в Git. Без ключа GeoKZ продолжает полностью работать с локальной базой, а scheduler фиксирует ошибку конкретного source без остановки приложения.

Подробно:

- `docs/CORE_DATASET_RU.md` — versioned baseline, manifest, checksum, install/status и rollback policy;
- `docs/EXTERNAL_API_KEYS_RU.md` — получение и настройка ключа;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md` — официальные `apiUri`, mapping, endpoint-ы, processing и правила именования ресурсов GeoKZ;
- `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md` — confirm/reject/manual-link/create-draft-field и правила безопасности review;
- `docs/KAZAKHSTAN_GEOLOGICAL_LICENSE_REVIEW_RU.md` — normalizer и record-level review лицензий;
- `docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md` — стабильная схема review queue для PySide6/web UI;
- `docs/EXTERNAL_SYNC_SCHEDULER_RU.md` — scheduler, Update All, due/retry и защита от параллельных run.

## Подсказки и помощники
Для сложных полей используются короткая подсказка, расширенное объяснение, пошаговый мастер и диагностическое предупреждение. Особенно важны подсказки для CRS, порядка X/Y, MD/TVD/TVDSS, ГИС, корреляции, Core Dataset и настройки внешних источников.

Актуальный статус реализации: `docs/PROJECT_PLAN_V0_2.md`.

## Визуальный корреляционный разрез
Для UI добавлен backend-owned view-model, который строится поверх уже рассчитанной корреляции, а не повторяет геологическую логику на клиенте:

```text
POST /api/v1/correlation/wells/view
```

Backend выбирает одну общую шкалу глубин с приоритетом `TVDSS → TVD → MD`. Реперы и интервалы, которые нельзя безопасно представить на выбранной шкале, возвращаются с `renderable=false` и не соединяются линиями автоматически. `correlation_lines` содержит готовые сегменты типов `MARKER` и `HORIZON`, а `warnings` — стабильные коды `DEPTH_REFERENCE_MISMATCH`, `NO_RENDERABLE_DATA`, `NO_CORRELATION_LINES` и другие диагностические состояния.

Клиент должен отображать `VerificationStatus` и предупреждения, но не должен самостоятельно пересчитывать глубины или создавать новые корреляционные связи. Полный контракт: `docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`.

## Полный demo workflow корреляции
Для проверки интерфейса без смешивания с production data используется единый сценарий:

```text
POST /api/v1/correlation/demo/workflow
```

Первый запрос содержит координату/radius и возвращает `stage=DISCOVERY`, `nearby_demo_wells`, `suggested_reference_well_id`, `can_build_cross_section` и обязательное `synthetic=true`. Затем UI выбирает одну reference well и 1–20 compared wells только из текущего `nearby_demo_wells` и повторяет тот же endpoint с `reference_well_id` и `well_ids`. При успешном выборе response имеет `stage=CROSS_SECTION_READY` и содержит готовый `cross_section`.

Dataset `synthetic-correlation-demo-v1` отделён от обычных скважин: даже production well в той же точке не попадает в demo selection. Неполный выбор, дубликаты, reference well внутри `well_ids` или UUID вне текущего discovery отклоняются HTTP `422`. Demo-набор создаётся командой `python -m scripts.seed_correlation_demo` и не является источником производственных фактов.

Подробный контракт и пошаговые примеры: `docs/DEMO_CORRELATION_WORKFLOW_RU.md`.
