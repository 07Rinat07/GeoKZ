# GeoKZ — реестр локальных и организационных CRS

## Назначение

GeoKZ поддерживает постоянное хранение подтверждённых систем координат организации для производственных X/Y. Это нужно для случаев, когда исходные материалы используют СК-42/Гаусса–Крюгера, локальную сетку предприятия, собственную проекцию или другой CRS, который нельзя безопасно определить только по числам координат.

Ключевое правило: GeoKZ **не угадывает CRS и порядок осей**. Перед использованием локальная система должна иметь точное определение `EPSG`, `WKT` или `PROJ`, ссылку/описание первичного источника и явное подтверждение.

## Модель данных

Миграция `20260904_0005` добавляет таблицу `organization_crs_definitions`. Для каждой записи сохраняются:

- стабильный `code`;
- названия RU/KK/EN;
- `definition_kind`: `EPSG`, `WKT` или `PROJ`;
- исходное `definition`;
- нормализованное `canonical_wkt`;
- authority name/code, если PROJ может их определить;
- `default_axis_order`;
- `source_reference`;
- notes;
- `is_confirmed`, `confirmed_by`, `confirmed_at`, `confirmation_note`;
- `is_active` и timestamps.

`confirmed_by` пока является явно переданным reviewer identifier. Полноценная привязка к authenticated user и AuditLog запланирована отдельным этапом; поэтому подтверждение CRS сейчас является техническим workflow, а не заменой корпоративного контроля доступа.

## Жизненный цикл

1. Пользователь создаёт CRS как неподтверждённую запись.
2. Backend проверяет определение через pyproj/PROJ и убеждается, что оно описывает projected CRS.
3. Сохраняются исходное определение и canonical WKT.
4. Специалист проверяет `source_reference`, definition и `axis_order` по паспорту координат, геодезической документации, проекту или официальному описанию.
5. Выполняется отдельное действие confirm.
6. Только активная запись с `is_confirmed=true` считается `selectable` и может использоваться через `registered_crs_code`.

Если изменены definition, definition kind, `default_axis_order` или `source_reference`, GeoKZ автоматически сбрасывает подтверждение. После этого систему необходимо проверить и подтвердить заново.

## REST API

Список записей:

```text
GET /api/v1/spatial/crs-definitions?lang=ru
```

Только доступные для выбора:

```text
GET /api/v1/spatial/crs-definitions?lang=ru&selectable_only=true
```

Создание:

```text
POST /api/v1/spatial/crs-definitions?lang=ru
```

Пример:

```json
{
  "code": "company-grid-01",
  "name_ru": "Локальная сетка предприятия 01",
  "name_kk": "Кәсіпорынның жергілікті торы 01",
  "name_en": "Company local grid 01",
  "definition_kind": "EPSG",
  "definition": "EPSG:32639",
  "default_axis_order": "x_easting_y_northing",
  "source_reference": "Паспорт системы координат проекта № ..."
}
```

Редактирование:

```text
PATCH /api/v1/spatial/crs-definitions/{definition_id}?lang=ru
```

Подтверждение:

```text
POST /api/v1/spatial/crs-definitions/{definition_id}/confirm?lang=ru
```

```json
{
  "confirmed_by": "geodesy-reviewer",
  "confirmation_note": "Сверено с паспортом координат проекта"
}
```

## Использование в координатном поиске

После подтверждения вместо длинного WKT/PROJ можно передать стабильный `registered_crs_code`:

```json
{
  "coordinate": {
    "type": "projected",
    "x": 711157.665,
    "y": 4851250.325,
    "registered_crs_code": "company-grid-01"
  },
  "radius_km": 5,
  "language": "ru",
  "limit": 25
}
```

Backend загружает подтверждённое определение и подтверждённый `axis_order`, преобразует точку в WGS84 и возвращает `registered_crs_code` в `resolved_coordinate`. Клиент не обязан повторять CRS definition в каждом запросе.

Для прямого ввода по-прежнему можно использовать поле `crs`, но тогда `axis_order` обязателен. Одновременно задавать `crs` и `registered_crs_code` нельзя.

## Ошибки и безопасность

- `404` — указанный registry code не найден;
- `409` — запись найдена, но не подтверждена или отключена;
- `422` — definition не распознаётся PROJ/pyproj, является geographic CRS для производственного X/Y, противоречит подтверждённому axis order или coordinate payload некорректен.

СК-42/Гаусса–Крюгера нельзя регистрировать только под названием «СК-42». Необходимо точное описание зоны/проекции/датума из подтверждённого источника. То же правило относится к локальным системам предприятия: название или похожие числовые диапазоны не являются доказательством CRS.

## Инварианты

- `source_reference` обязателен;
- `axis_order` хранится как часть подтверждённого определения;
- непроверенные записи никогда не участвуют в преобразовании координат;
- изменение критичных параметров снимает `is_confirmed`;
- canonical WKT хранится для воспроизводимости;
- локальная CRS не изменяет исходные X/Y пользователя и не подменяет provenance;
- UI должен показывать статус подтверждения и не предлагать неподтверждённые записи как доступные для выбора.
