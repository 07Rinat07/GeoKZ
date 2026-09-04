# GeoKZ — demo workflow корреляционного разреза (RU)

## Назначение

`POST /api/v1/correlation/demo/workflow` предоставляет безопасный учебный сценарий от координаты до готового визуального корреляционного разреза. Он предназначен для проверки UX, API и будущего PySide6/web-клиента на синтетических данных и не является способом получения производственных геологических фактов.

Demo workflow не вводит отдельную геологическую логику. Он оркестрирует уже существующие сервисы GeoKZ:

1. `CoordinateResolver` безопасно преобразует исходные координаты в WGS84;
2. `SpatialSearchService.search_nearby_wells()` выполняет PostGIS-поиск;
3. workflow оставляет только скважины официально помеченного demo dataset;
4. пользователь выбирает опорную и минимум одну сравниваемую скважину;
5. `WellCrossSectionViewService` строит тот же backend-owned cross-section contract, что и `POST /api/v1/correlation/wells/view`.

## Важное ограничение

Dataset `synthetic-correlation-demo-v1` содержит учебные synthetic wells. Response всегда содержит `synthetic=true` и локализованное предупреждение. Эти данные нельзя цитировать как сведения о реальных месторождениях, запасах, глубинах, коллекторах или результатах испытаний.

Workflow специально исключает обычные production wells даже тогда, когда они находятся в том же радиусе поиска. В demo selection допускаются только записи, одновременно относящиеся к demo dataset и имеющие внутренний demo well identifier.

## Шаг 1 — поиск demo-скважин

Пример запроса:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "ru",
  "limit": 10
}
```

Endpoint:

```text
POST /api/v1/correlation/demo/workflow
```

На первом шаге `reference_well_id` не задаётся, а `well_ids` остаётся пустым. Ответ имеет:

```text
stage = DISCOVERY
```

Ключевые поля:

- `resolved_coordinate` — безопасно преобразованная рабочая WGS84-точка;
- `nearby_demo_wells` — только synthetic/demo скважины в заданном радиусе, отсортированные по расстоянию;
- `suggested_reference_well_id` — ближайшая demo-скважина как UI-подсказка, а не геологическое решение;
- `can_build_cross_section` — `true`, когда найдено минимум две demo-скважины;
- `selection_contract` — стабильный backend contract следующего шага;
- `warning` — обязательное предупреждение о synthetic data;
- `selection_note` — локализованная инструкция выбора.

`nearby_demo_wells` сохраняет `distance_m`, карточку скважины, известные интервалы и `passport_path`. Каждый элемент явно содержит `synthetic=true`.

## Шаг 2 — выбор и разрез

Пользователь выбирает одну опорную скважину и минимум одну сравниваемую только из текущего `nearby_demo_wells`. Затем отправляет тот же запрос повторно:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "ru",
  "limit": 10,
  "reference_well_id": "<UUID опорной demo-скважины>",
  "well_ids": [
    "<UUID сравниваемой demo-скважины>"
  ]
}
```

Успешный ответ имеет:

```text
stage = CROSS_SECTION_READY
```

и дополнительно содержит:

- `selection.reference_well_id`;
- `selection.compared_well_ids`;
- `cross_section` — полный `WellCrossSectionViewResponse`.

`cross_section` использует общий depth reference с приоритетом `TVDSS → TVD → MD`, `renderable`, `MARKER`/`HORIZON` lines, warnings и `VerificationStatus`. Demo workflow не меняет эти правила.

## Правила выбора

Backend отклоняет запрос с HTTP `422`, если:

- задан `reference_well_id`, но `well_ids` пуст;
- заданы `well_ids`, но отсутствует `reference_well_id`;
- `well_ids` содержит дубликаты;
- опорная скважина также включена в `well_ids`;
- хотя бы одна выбранная скважина не принадлежит текущему списку найденных demo wells;
- координата/CRS не может быть безопасно разрешена.

Это означает, что клиент не должен хранить «доверенный» список demo UUID самостоятельно между несовместимыми поисками. Повторный запрос всегда проверяется относительно текущих coordinate/radius/limit и локальной базы.

## Почему production wells исключаются

Demo workflow предназначен для воспроизводимой проверки интерфейса. Наличие реальной скважины возле demo-координаты не должно случайно смешивать synthetic и production data. Поэтому backend сначала определяет разрешённый demo dataset, затем передаёт конкретные demo well IDs в PostGIS nearby query.

Обычный производственный workflow должен использовать универсальные endpoints:

```text
POST /api/v1/spatial/nearby
POST /api/v1/correlation/wells/view
```

Demo endpoint не заменяет их.

## Seed demo dataset

Локальный synthetic dataset создаётся командой:

```text
python -m scripts.seed_correlation_demo
```

Текущий demo-набор содержит четыре скважины, реперы `R1`/`R2` и горизонт `J-II`. Dataset code хранится централизованно как `synthetic-correlation-demo-v1`, чтобы seed script и runtime workflow использовали одно значение.

Seed должен оставаться идемпотентным: повторный запуск не должен создавать дубли demo entities, wells, markers или intervals.

## UI contract

PySide6/web-клиенту рекомендуется:

1. показать поле координаты и radius;
2. вызвать demo workflow без selection;
3. показать только `nearby_demo_wells`;
4. отдельно выделить `suggested_reference_well_id` как рекомендацию UI;
5. разрешить выбрать ровно одну reference well и 1–20 compared wells;
6. повторить тот же endpoint с selection;
7. отрисовать `cross_section` по `docs/CROSS_SECTION_VIEW_CONTRACT_RU.md`;
8. постоянно отображать synthetic warning.

Клиент не должен самостоятельно добавлять production wells в demo selection, подменять dataset marker, пересчитывать PostGIS distance, глубины или correlation lines.

## Тестирование

Definition of Done включает реальный PostgreSQL/PostGIS integration test. Он проверяет полный HTTP workflow: seed demo dataset, наличие рядом отдельной production fixture well, discovery только четырёх demo wells, построение TVDSS cross-section и отказ при попытке выбрать production well.

Таким образом тест подтверждает не только сериализацию response, но и ключевую границу безопасности между synthetic demo и обычными данными GeoKZ.
