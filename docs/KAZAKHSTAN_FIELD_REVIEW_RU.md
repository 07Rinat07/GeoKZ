# GeoKZ — проверка и сопоставление внешних месторождений (RU)

Актуальность: 2026-09-04. Версия: `0.2-dev`.

## Назначение

После синхронизации ресурса `kz-egov-oil-gas-fields` (`apiUri=stat_kgn_117`, `v10`) GeoKZ сохраняет записи в RAW/staging, затем `process` нормализует название месторождения и предлагает возможную связь с существующим `GeologicalEntity(object_type="field")`.

Автоматическое совпадение по имени или alias **не является экспертным подтверждением**. Оно создаёт только `ExternalEntityLink(status=REVIEW_REQUIRED)`.

## 1. Получить очередь проверки

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Параметры:

- `limit` — от 1 до 200;
- `offset` — смещение.

Для каждой записи возвращаются RAW payload, normalized payload, статус записи и возможные связи с существующими месторождениями.

## 2. Подтвердить предложенную связь

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
```

Тело:

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Подтверждено по источникам"
}
```

Результат:

- выбранный `ExternalEntityLink` → `VERIFIED`;
- ExternalRecord → `ACCEPTED`;
- другие незавершённые автоматические кандидаты этой записи → `REJECTED`;
- существующий `GeologicalEntity` не переписывается данными внешнего API.

Если для записи уже существует другая `VERIFIED` связь, система не создаёт вторую подтверждённую связь и требует отдельного пересмотра.

## 3. Отклонить кандидата

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
```

Тело содержит обязательные `reviewer` и `comment`. Причина отклонения сохраняется. Отклонение одного кандидата не закрывает запись автоматически, если её ещё требуется связать вручную или проверить дальше.

## 4. Вручную связать с существующим месторождением

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
```

Пример:

```json
{
  "entity_id": "UUID существующего GeologicalEntity",
  "reviewer": "Sarmuldin Rinat",
  "comment": "Название в государственном реестре отличается от рабочего названия"
}
```

GeoKZ разрешает такую связь только с `object_type=field`. Связь получает `match_method=MANUAL` и `status=VERIFIED`, а выбранный существующий геологический объект остаётся со своим текущим `verification_status`.

## 5. Создать новое месторождение из UNMATCHED

Только если `process` присвоил записи `matching.status=UNMATCHED`, пользователь может явно создать новый объект:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

Пример:

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Создать карточку для дальнейшей геологической проверки",
  "name_ru": "Название",
  "name_kk": "Атауы",
  "name_en": "Name"
}
```

Критическое правило: новый `GeologicalEntity` создаётся **только со статусом `DRAFT`**. Подтверждённая связь с официальной записью не превращает геологический объект в `VERIFIED`. Его координаты, геологию, стратиграфию, скважины, запасы и другие свойства необходимо подтверждать отдельными источниками и экспертной проверкой.

В `geological_context` сохраняются provenance-поля: источник, UUID внешней записи и upstream external id.

## 6. Защита решения эксперта

После ручного решения связь считается reviewer-locked, если она `VERIFIED`/`REJECTED`, создана методом `MANUAL`, содержит `verified_by` или review comment. Повторная внешняя синхронизация и повторный `process` не имеют права молча заменить такое решение.

Если upstream-название изменилось, незавершённые автоматические `REVIEW_REQUIRED` связи могут быть пересчитаны, но ручные решения остаются неизменными.

## 7. Ограничение текущей версии

В `v0.2-dev` полноценная пользовательская авторизация и AuditLog ещё не реализованы. Поэтому `reviewer` передаётся явно в теле запроса. До production-релиза это будет заменено идентификатором авторизованного пользователя, а действия review будут записываться в audit/revision history.

## 8. Рекомендуемый workflow

```text
register
  → schema
  → sync
  → process
  → review queue
      ├─ confirm candidate
      ├─ reject candidate
      ├─ manual link
      └─ create DRAFT field from UNMATCHED
  → дальнейшая геологическая проверка объекта
  → только затем VERIFIED master data
```

Связанные документы:

- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`;
- `docs/EXTERNAL_API_KEYS_RU.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/PROJECT_PLAN_V0_2.md`.
