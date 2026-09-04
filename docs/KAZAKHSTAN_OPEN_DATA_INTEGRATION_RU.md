# GeoKZ — интеграция с Kazakhstan Open Data / data.egov.kz (RU)

Актуальность: 2026-09-04.

## 1. Официальная терминология data.egov.kz

GeoKZ использует термины портала без переименования:

- `apiUri` — технический индекс/идентификатор набора на `data.egov.kz`;
- `version` — версия ресурса, например `v10`;
- `fields` — технические имена полей набора;
- `labelRu`, `labelKk`, `labelEn` — пользовательские подписи полей из метаданных;
- `source` — JSON-параметр запроса API v4, описывающий `from`, `size`, `query`, `sort` и другие параметры Elasticsearch-поиска.

Пример ресурса GeoKZ:

```text
GeoKZ code:  kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

`GeoKZ code` — наш стабильный идентификатор connector-а. Он не заменяет и не изменяет официальный `apiUri`.

## 2. Официальные REST-шаблоны

Для ресурса `{apiUri}` версии `{version}` используются следующие официальные формы:

```text
Metadata:
GET https://data.egov.kz/meta/{apiUri}/{version}

Mapping / структура полей:
GET https://data.egov.kz/api/v4/mapping/{apiUri}/{version}

Данные API v4:
GET https://data.egov.kz/api/v4/{apiUri}/{version}?source={JSON}

Detailed API:
GET https://data.egov.kz/api/detailed/{apiUri}/{version}?source={JSON}
```

Для фактической выгрузки данных API v4 GeoKZ передаёт пользовательский API key согласно требованиям портала. Ключ хранится только в `GEOKZ_EGOV_API_KEY`.

Официальное описание API: `https://data.egov.kz/pages/samples`.

## 3. Как GeoKZ называет внешние ресурсы

### 3.1 `code`

Внутренний стабильный slug GeoKZ:

```text
kz-egov-<domain>
```

Примеры:

```text
kz-egov-oil-gas-fields
kz-egov-geological-study-licenses
```

Правила:

- lowercase;
- ASCII;
- kebab-case;
- начинается с `kz-egov-` для `data.egov.kz`;
- отражает смысл ресурса, а не текущую версию;
- версия в `code` не включается.

### 3.2 `api_uri`

Всегда хранится в точности как официальный `apiUri` портала:

```text
stat_kgn_117
zher_koinauyn_geologiyalyk_zer2
```

Не переводить, не сокращать и не заменять собственным названием.

### 3.3 `version`

Хранится отдельно и без преобразования:

```text
v10
v6
```

### 3.4 `record_type`

Внутренний тип нормализуемой записи GeoKZ:

```text
oil_gas_field
geological_study_license
```

Правила:

- английский язык;
- lowercase;
- singular;
- snake_case;
- описывает сущность одной записи, а не название всего набора.

### 3.5 Поля RAW-записи

Технические ключи, полученные с `data.egov.kz`, сохраняются в `raw_payload` без переименования. Нормализованные поля GeoKZ создаются отдельно в `normalized_payload`/domain model.

Это позволяет повторно обработать данные при изменении mapping-а и сохраняет provenance.

## 4. Правильный порядок подключения нового ресурса

1. Найти официальный набор на `data.egov.kz`.
2. Получить его `apiUri` и актуальную `version`.
3. Проверить metadata:

```text
GET /meta/{apiUri}/{version}
```

4. Проверить mapping:

```text
GET /api/v4/mapping/{apiUri}/{version}
```

5. Сверить технические имена и типы полей.
6. Сделать небольшой запрос, например `source={"size":5}`.
7. Выбрать устойчивое identity-поле. Если портал менял название колонки — задать alias group.
8. Добавить ресурс в `app/integrations/kazakhstan_open_data.py`.
9. Добавить RU/KK/EN названия и описания.
10. Добавить тесты registry, metadata/mapping contract и parsing.
11. Проверить лицензию/условия использования и attribution.
12. Зарегистрировать ресурс в GeoKZ.
13. Выполнить первую синхронизацию только в RAW/staging.
14. После проверки реализовать normalization/matching/review.

## 5. Проверка ресурса через GeoKZ

Каталог:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

GeoKZ возвращает для каждого ресурса:

- `code`;
- `api_uri`;
- `version`;
- `record_type`;
- `metadata_url`;
- `mapping_url`;
- `data_url_template`;
- `detailed_url_template`;
- наличие API key;
- состояние регистрации.

Проверка официальной schema/mapping до загрузки:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Ответ содержит:

```text
code
api_uri
version
metadata
mapping
```

Этот endpoint не нормализует и не публикует данные — он нужен для проверки контракта внешнего ресурса.

## 6. Регистрация и синхронизация

Регистрация известных ресурсов:

```text
POST /api/v1/integrations/kazakhstan/register
```

Ручная синхронизация:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

Поток данных:

```text
data.egov.kz
  → metadata/mapping validation
  → RAW/staging
  → checksum/diff
  → normalization
  → matching
  → review
  → verified GeoKZ master data
```

## 7. Уже подключённые ресурсы

### Нефтегазовые месторождения Республики Казахстан

```text
code:        kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

### Лицензии на геологическое изучение недр

```text
code:        kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

## 8. Правило совместимости

Если портал выпускает новую версию `v11`, GeoKZ не меняет `code`. Меняются `version`, endpoint-ы и при необходимости normalization mapping. Перед переключением версии обязательно сравниваются metadata/mapping и прогоняются contract tests.

## 9. Связанные документы

- `docs/EXTERNAL_API_KEYS_RU.md` — получение и безопасное хранение API key;
- `docs/USER_GUIDE_RU.md` — пользовательская работа с источниками;
- `docs/PROJECT_PLAN_V0_2.md` — актуальный roadmap;
- `docs/DOCUMENTATION_POLICY.md` — правило синхронного обновления RU/KK/EN документации.
