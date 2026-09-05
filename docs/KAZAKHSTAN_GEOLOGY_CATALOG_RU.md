# GeoKZ — расширение официального геологического каталога Казахстана (RU)

Статус контракта: `v0.3`, проверка официальных ресурсов выполнена 2026-09-05.

## Цель

GeoKZ расширяет официальный каталог источников Казахстана постепенно: сначала источник становится видимым и проверяемым, затем для него реализуются typed normalizer, правила сопоставления и review workflow, и только после этого включается синхронизация RAW-записей. Такой порядок не позволяет новому набору данных автоматически попасть в trusted master data только потому, что он опубликован на `data.egov.kz`.

Базовая локальная БД GeoKZ и Core Dataset продолжают работать без внешних сервисов и без `GEOKZ_EGOV_API_KEY`.

## Текущий официальный каталог

Уже поддерживаемые sync/process/review источники:

- `kz-egov-oil-gas-fields` → `apiUri=stat_kgn_117`, фиксированная версия `v10`, `record_type=oil_gas_field`;
- `kz-egov-geological-study-licenses` → `apiUri=zher_koinauyn_geologiyalyk_zer2`, фиксированная версия `v6`, `record_type=geological_study_license`.

Новые официальные кандидаты Комитета геологии:

- `kz-egov-solid-mineral-fields` → `apiUri=stat_kgn_118`, «Твердые полезные ископаемые Республики Казахстан»;
- `kz-egov-groundwater-fields` → `apiUri=stat_kgn_120`, «Месторождения подземных вод Республики Казахстан».

Официальные страницы:

```text
https://data.egov.kz/datasets/view?index=stat_kgn_118
https://data.egov.kz/datasets/view?index=stat_kgn_120
```

Для этих двух наборов GeoKZ **не фиксирует выдуманный номер версии**. В каталоге отображается политика `LATEST_MAPPING`.

## Политика версии `LATEST_MAPPING`

Портал Open Data Kazakhstan позволяет получить mapping набора без указания версии. GeoKZ использует этот официальный mapping endpoint для определения опубликованной версии:

```text
GET https://data.egov.kz/api/v4/mapping/{apiUri}
```

Connector рассматривает только ключи формата `vN`, где `N` — целое число, и выбирает максимальное числовое значение. Поэтому `v10` корректно новее `v2`; произвольные ключи вроде `preview` игнорируются. Определенная версия кешируется на время жизни connector и затем одинаково используется для metadata, mapping и data requests.

Если mapping не содержит ни одной опубликованной версии `vN`, операция завершается ошибкой `ExternalSourceProtocolError`. GeoKZ не делает предположений о версии и не переключается на неизвестный endpoint.

Для уже стабилизированных наборов применяется политика `PINNED`: `stat_kgn_117/v10` и `zher_koinauyn_geologiyalyk_zer2/v6` продолжают использовать явную проверенную версию.

## Регистрация и просмотр каталога

```text
POST /api/v1/integrations/kazakhstan/register
GET  /api/v1/integrations/kazakhstan/catalog?lang=ru
GET  /api/v1/integrations/kazakhstan/{code}/schema
```

`register` создаёт локальные `ExternalDataSource` записи для всех известных официальных наборов. Это не означает разрешение синхронизации.

Для `stat_kgn_118` и `stat_kgn_120` первоначальное состояние специально безопасное:

```text
enabled=false
sync_mode=MANUAL
version=LATEST_MAPPING
sync_supported=false
processing_supported=false
```

В `source_config` сохраняются `api_uri`, `record_type`, official/metadata/mapping/data URL templates, `version_policy`, а также флаги `sync_supported` и `processing_supported`.

## Schema inspection до включения sync

Endpoint:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/schema
GET /api/v1/integrations/kazakhstan/kz-egov-groundwater-fields/schema
```

сначала определяет актуальную версию через mapping, затем читает metadata и versioned mapping. Для этой операции eGov API key не нужен. Ответ возвращает уже **разрешённую фактическую версию**, а не `LATEST_MAPPING`.

Это позволяет разработать typed normalizer по реальной текущей схеме без hard-coded догадок. Перед каждым изменением normalizer необходимо снова сверить mapping, потому что технические имена колонок у открытых наборов могут изменяться.

## Почему синхронизация пока заблокирована

Наличие официального набора недостаточно для безопасного автоматического импорта. Для каждого нового `record_type` до включения sync нужны:

1. точная схема и identity strategy;
2. typed normalizer с диагностикой неизвестной/неоднозначной схемы;
3. provenance-preserving normalized payload;
4. match policy к существующим `GeologicalEntity` и aliases;
5. review queue и reviewer-locked decisions;
6. правило создания новых объектов только как `DRAFT`;
7. unit + PostgreSQL/PostGIS integration tests;
8. RU/KK/EN документация.

Поэтому прямой вызов:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/sync
```

пока завершается контролируемой конфигурационной ошибкой. Даже если локальную запись источника вручную включить, `ExternalConnectorRegistry` не отдаст sync-ready connector до перевода `sync_supported=true` в кодовом контракте.

`Update All` и scheduler также безопасны: disabled source пропускается; catalog-only источник, принудительно включенный в БД, получает `SKIPPED_UNSUPPORTED`, а не RAW-import.

## API key

Metadata/mapping/schema inspection доступны без ключа. Фактическое получение записей через API v4 требует локального секрета:

```env
GEOKZ_EGOV_API_KEY=...
```

Ключ не должен попадать в Git, документацию, логи или desktop settings. PySide6 не хранит eGov key и работает только через GeoKZ API.

## Инварианты GeoKZ

- `apiUri` сохраняется в точном upstream-виде;
- отсутствие известной версии не компенсируется догадкой;
- RAW и normalized payload разделены;
- новые внешние данные не перезаписывают verified master data автоматически;
- `ExternalEntityLink=VERIFIED` не означает `GeologicalEntity=VERIFIED`;
- новый геологический объект из review создаётся как `DRAFT`;
- upstream deletion в будущем становится tombstone/inactive, а не hard delete master data;
- внешний источник является optional enrichment layer, а не обязательной зависимостью приложения.

## Следующий шаг

После этого catalog-only среза первым переводится в рабочий pipeline `kz-egov-solid-mineral-fields` (`stat_kgn_118`): schema inspection → typed normalizer → matching/review → tests → только затем `sync_supported=true`. Набор подземных вод (`stat_kgn_120`) идёт следующим отдельным срезом, чтобы не смешивать разные геологические semantics.

Автор: **Sarmuldin Rinat — ura07srr@gmail.com**.
