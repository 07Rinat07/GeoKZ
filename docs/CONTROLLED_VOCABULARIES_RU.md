# GeoKZ — контролируемые геологические словари (RU)

Статус: foundation `v0.3`, 2026-09-05.

## Назначение

GeoKZ вводит отдельный persistent-реестр контролируемых терминов для четырёх категорий: `lithology`, `marker_type`, `property_kind` и `unit`. Цель — дать API, импортерам, будущему PySide6-клиенту и внешним коннекторам стабильные canonical codes, не превращая исходный текст источника в «исправленную» версию.

Главное правило: **RAW/source wording сохраняется отдельно и не переписывается словарём**. Например, импортированный LAS mnemonic, авторское описание литологии или исходная единица измерения остаются в исходных полях/RAW payload. Контролируемый словарь добавляет нормализованный код только как отдельный слой интерпретации.

## Модель

Таблица `controlled_vocabulary_terms` хранит:

- `vocabulary` — один из четырёх стабильных кодов;
- `code` — canonical GeoKZ code внутри категории;
- `name_ru`, `name_kk`, `name_en` — обязательные отображаемые названия;
- `aliases` — допустимые точные варианты написания для безопасного сопоставления;
- `description` — необязательное пояснение;
- `source_reference` — происхождение/основание термина;
- `metadata` — расширяемые технические атрибуты, например `symbol`, `quantity_kind`, типичные mnemonics;
- `is_active` — можно ли использовать термин в новых нормализациях.

Уникальность обеспечивается парой `(vocabulary, code)`. Словарь не использует один огромный Python Enum для геологии: термины должны расширяться без изменения прикладного кода и без смешивания разных предметных категорий.

## API

Каталог категорий:

```text
GET /api/v1/vocabularies?lang=ru
```

Список терминов одной категории:

```text
GET /api/v1/vocabularies/lithology/terms?lang=ru
GET /api/v1/vocabularies/unit/terms?lang=ru&include_inactive=false
```

Безопасное пакетное разрешение исходных значений:

```text
POST /api/v1/vocabularies/property_kind/resolve?lang=ru
```

Тело:

```json
{
  "values": ["GR", "Gamma ray", "неизвестный параметр"]
}
```

Ответ для каждого входного значения содержит `RESOLVED`, `UNRESOLVED` или `AMBIGUOUS`. Автоматического fuzzy matching на этом этапе нет: GeoKZ использует case-insensitive точное совпадение после нормализации пробелов по `code`, трём названиям и aliases. Если один alias неожиданно относится к нескольким терминам, результат становится `AMBIGUOUS`, а не выбирается произвольно.

## Bootstrap

Начальный словарь находится в:

```text
data/bootstrap/controlled_vocabularies.json
```

Это **initial internal dictionary**, а не утверждение о полноте геологической классификации Казахстана. Он содержит минимальный набор терминов для литологии, типов реперов, well-log/property kinds и единиц измерения. Любое производственное расширение должно проходить предметную проверку и иметь `source_reference`.

Загрузка/повторное обновление выполняется идемпотентным скриптом:

```text
python -m scripts.seed_controlled_vocabularies
```

Скрипт делает upsert по `(vocabulary, code)`. Schema migration и dataset seeding разделены: Alembic создаёт структуру таблицы, а bootstrap наполняет данные отдельно.

## Правила безопасности и provenance

1. Контролируемый термин не удаляет исходное значение из документа, LAS/DLIS/WITSML, внешнего API или экспертного ввода.
2. `source_reference` обязателен даже для bootstrap-термов.
3. Неактивный термин не участвует в обычном resolve.
4. Fuzzy/semantic matching в дальнейшем может создавать только candidate для review, но не должен автоматически подменять canonical code.
5. Запись/редактирование словарей через публичный API пока намеренно отсутствует. Admin write API появится после Authentication + AuditLog/revisions, чтобы изменения терминологии имели автора и историю.
6. Единицы измерения имеют canonical code и metadata `symbol`/`quantity_kind`; числовые конверсии не выполняются только по похожей строке единицы без явного правила преобразования.

## Следующий шаг

После foundation canonical codes будут подключены к предметным моделям **без удаления raw-полей**: `WellInterval/CoreSample` для литологии, `WellMarker` для marker type, `WellLogCurve` для property kind/unit и rate-unit fields для испытаний/интервалов. Миграция должна быть обратно совместимой, а normalization должен явно различать raw value, resolved canonical code и unresolved/review-required состояние.
