# GeoKZ Core Dataset — RU

## Назначение

GeoKZ Core Dataset — независимо версионируемый базовый набор данных, который поставляется вместе с приложением и может устанавливаться в PostgreSQL/PostGIS отдельно от миграций схемы Alembic.

Версии разделены намеренно:

- версия приложения GeoKZ;
- Alembic revision / схема БД;
- версия GeoKZ Core Dataset;
- версии и checkpoints внешних providers.

Обновление содержимого не должно требовать data-migration внутри Alembic.

## Текущий bundled snapshot

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
namespace:       geokz-core:
```

Первый bootstrap намеренно минимален: он содержит внутреннюю metadata-запись источника и country-level запись «Республика Казахстан» без утверждения границы/геометрии. `entities.jsonl` и `facts.jsonl` пока пусты. GeoKZ не добавляет вымышленные геологические факты только ради заполнения baseline.

`geokz-core:source:bootstrap` — техническая metadata-запись Core Dataset, а не геологический evidence source.

## Manifest и файлы

Bundle расположен в `data/bootstrap/core_dataset/` и содержит:

```text
manifest.json
sources.jsonl
regions.geojson
entities.jsonl
facts.jsonl
```

`manifest.json` хранит независимую версию набора, `schema_version`, namespace, зависимости и SHA-256 каждого файла. Каждый required-файл должен находиться внутри bundle root; absolute path и `..` отклоняются.

Перед любой записью в БД GeoKZ проверяет:

1. JSON/Pydantic schema manifest-а;
2. поддерживаемый `schema_version`;
3. отсутствие duplicate file path/kind;
4. отсутствие path traversal;
5. наличие required-файлов;
6. SHA-256 каждого файла;
7. типы payload;
8. уникальность `external_id` внутри каждого типа;
9. обязательный namespace `geokz-core:`;
10. ссылки parent/source/entity/related facts внутри bundle.

Поле `minimum_app_version` в schema v1 является metadata для отображения и будущего compatibility policy. Жёсткий semantic-version gate пока не выполняется; фактический compatibility gate v1 — `schema_version`.

## Транзакционность и rollback

Importer выполняет все upsert-операции одного bundle в одной SQLAlchemy transaction. `CoreDatasetState` записывается только в конце успешного импорта. При исключении выполняется rollback, поэтому частично установленный baseline не считается допустимым состоянием.

Повторная установка того же manifest SHA-256 идемпотентна: importer возвращает `changed=false` и не создаёт дубликаты.

Core Dataset использует собственный namespace `geokz-core:`. Это отделяет управляемые baseline-записи от пользовательских, внешних и экспертно проверенных объектов. Текущий importer не использует совпадение по произвольному имени как право переписать существующий master data.

## REST API

Статус bundled и установленной версии:

```text
GET /api/v1/core-dataset/status
```

Ответ содержит `bundled_version`, `schema_version`, manifest SHA-256, зависимости, installed state и `update_available`.

Проверка без записи:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=ru
```

Установка bundled snapshot:

```text
POST /api/v1/core-dataset/install?lang=ru
```

HTTP endpoint намеренно не принимает произвольный путь к manifest: сервер устанавливает только доверенный bundled snapshot. Для административной работы с локальным bundle используется CLI.

## CLI

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Для локальной диагностики CLI также принимает явный путь к `manifest.json` как позиционный аргумент.

## About

`GET /api/v1/about` отдельно показывает:

```text
core_dataset_version
core_dataset_schema_version
```

Это bundled version, а не утверждение, что она уже установлена в текущую БД. Фактическое состояние БД проверяется через `/api/v1/core-dataset/status`.

## Правила будущих обновлений

Следующие snapshots должны:

- иметь новую `dataset_version`;
- сохранять стабильные `external_id` для одной и той же сущности;
- содержать доказуемые source/provenance данные для геологических фактов;
- проходить checksum и reference validation;
- не превращать внешние или AI-derived данные в verified master автоматически;
- обновляться независимо от `.exe`/app version, если schema совместима.

Подпись bundles, download/update channel и rollback на предыдущую установленную версию являются последующими этапами; schema v1 уже отделяет dataset lifecycle от Alembic lifecycle.
