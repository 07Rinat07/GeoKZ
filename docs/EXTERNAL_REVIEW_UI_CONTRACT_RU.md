# GeoKZ — UI/View-Model контракт очереди external review (RU)

Актуальность: 2026-09-04. Ветка разработки: `feature/external-review-ui-contract-v0.3`.

## Назначение

Этот контракт предназначен для будущего PySide6-клиента и других UI GeoKZ. Клиент не должен самостоятельно разбирать RAW payload, вычислять разрешённые review-действия или собирать URL для confirm/reject/manual-link/create-draft-field. Backend возвращает готовую, типизированную и локализованную view-model очереди.

Основной endpoint:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=ru&limit=100&offset=0
```

Поддерживаемые языки: `ru`, `kk`, `en`.

Технический endpoint `GET .../review` остаётся доступным для низкоуровневой работы и обратной совместимости. Для пользовательского интерфейса следует использовать `GET .../review/view`.

## Верхний уровень ответа

View-model содержит:

- `source_code` — стабильный внутренний код источника;
- `language` — язык локализованных полей;
- `title` — заголовок очереди для UI;
- `policy_note` — обязательное предупреждение о правилах верификации;
- `total_pending` — общее количество записей `REVIEW_REQUIRED`;
- `returned_count` — количество записей в текущей странице;
- `limit`, `offset` — параметры пагинации;
- `has_more` — есть ли следующая страница;
- `records` — записи очереди.

Пример:

```json
{
  "source_code": "kz-egov-oil-gas-fields",
  "language": "ru",
  "title": "Проверка внешних нефтегазовых месторождений",
  "policy_note": "Подтверждение связи с официальной записью не делает геологический объект VERIFIED...",
  "total_pending": 42,
  "returned_count": 20,
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "records": []
}
```

## Запись очереди

Каждый элемент `records` содержит:

- `record_id` — UUID внешней записи GeoKZ;
- `external_id` — идентификатор upstream;
- `display_name` — безопасное отображаемое название;
- `status` — статус `ExternalRecord`;
- `matching_status` — нормализованный статус matching;
- `raw_payload` — исходная запись без переименования технических полей;
- `normalized_payload` — нормализованная интерпретация GeoKZ;
- `candidates` — кандидаты связи с существующими объектами;
- `actions` — действия уровня записи.

Стабильные значения `matching_status`:

```text
CANDIDATE
AMBIGUOUS
UNMATCHED
REVIEWER_LOCKED
UNAVAILABLE
UNKNOWN
```

`UNKNOWN` используется как безопасный fallback, если backend встретил новое или неизвестное значение. UI не должен падать из-за неизвестного будущего статуса.

## Кандидат связи

Каждый элемент `candidates` содержит:

- `link_id`;
- `entity_id`;
- `entity_display_name` — локализованное имя с fallback RU/KK/EN;
- `entity_verification_status` — отдельный verification status геологического объекта;
- `match_method`;
- `match_confidence`;
- `status` связи;
- `verified_by` и `review_comment`, если решение уже было принято;
- `actions` для данного кандидата.

Критическое правило: `entity_verification_status` и статус `ExternalEntityLink` — разные сущности. `ExternalEntityLink=VERIFIED` означает только подтверждение соответствия внешней записи и объекта GeoKZ. Это не делает геологический объект `VERIFIED` и не подтверждает его координаты, запасы, стратиграфию, литологию или другие свойства.

## Descriptor действия

UI получает действие как объект, а не вычисляет его самостоятельно:

```json
{
  "code": "REJECT_LINK",
  "label": "Отклонить связь",
  "method": "POST",
  "path": "/api/v1/integrations/kazakhstan/.../reject",
  "enabled": true,
  "disabled_reason": null,
  "required_fields": ["reviewer", "comment"],
  "optional_fields": []
}
```

Стабильные коды действий:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Клиент должен использовать `code` для логики, `label` только для отображения, `path` как выданный backend endpoint, `enabled` для доступности кнопки, а `required_fields`/`optional_fields` — для формы ввода.

## Правила доступности действий

`CONFIRM_LINK` и `REJECT_LINK` доступны только для unresolved automatic candidate (`REVIEW_REQUIRED` или `AUTO_MATCHED`). Если связь уже reviewer-locked, backend возвращает `enabled=false` и локализованный `disabled_reason`.

`MANUAL_LINK` доступен для pending-записи и требует `entity_id` и `reviewer`.

`CREATE_DRAFT_FIELD` доступен только при `matching_status=UNMATCHED`. Для `CANDIDATE`, `AMBIGUOUS`, `REVIEWER_LOCKED`, `UNAVAILABLE` и `UNKNOWN` backend возвращает действие, но с `enabled=false`. Это позволяет UI отображать стабильную кнопку без дублирования бизнес-правил.

Созданный из внешней записи объект всегда начинается со статуса `DRAFT`.

## Пагинация

UI передаёт `limit` от 1 до 200 и `offset >= 0`. Для загрузки следующей страницы рекомендуется использовать:

```text
next_offset = offset + returned_count
```

и выполнять следующий запрос только если `has_more=true`.

`total_pending` считается backend по реальной очереди `ExternalRecord(status=REVIEW_REQUIRED)` и не должен вычисляться клиентом по длине текущей страницы.

## Рекомендуемый PySide6 flow

```text
Открыть экран External Review
  → GET review/view?lang=<текущий язык>
  → отрисовать records/candidates
  → отрисовать actions по descriptor-ам
  → пользователь выбирает действие
  → UI запрашивает только required/optional fields
  → POST на action.path
  → после успешного ответа обновить текущую страницу review/view
```

UI не должен:

- автоматически подтверждать match;
- превращать `VERIFIED` link в `VERIFIED` geological entity;
- строить endpoint-ы из строк вручную, если backend уже вернул `path`;
- активировать действие при `enabled=false`;
- скрывать `policy_note` на review-экране;
- переписывать RAW payload.

## Совместимость

View-model добавлена отдельным endpoint и не меняет форму существующего `GET .../review`. Это позволяет постепенно подключать PySide6 и web UI без breaking change для технических клиентов.

При расширении review на другие типы ресурсов контракт должен сохранять общие поля очереди и action descriptors. Специфичные поля могут добавляться только расширением схемы без изменения смысла существующих кодов.

## Связанные документы

- `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md` — бизнес-правила review;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md` — подключение официального источника;
- `docs/USER_GUIDE_RU.md` — пользовательский workflow;
- `docs/PROJECT_PLAN_V0_2.md` — актуальный roadmap.
