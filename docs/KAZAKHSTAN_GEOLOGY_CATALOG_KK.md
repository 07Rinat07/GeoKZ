# GeoKZ — Қазақстанның ресми геологиялық каталогын кеңейту (KK)

Контракт күйі: `v0.3`, ресми ресурстар 2026-09-05 күні тексерілді.

## Мақсаты

GeoKZ Қазақстанның ресми дереккөздерін біртіндеп қосады: алдымен дереккөз каталогта көрінеді және оның schema/metadata ақпараты тексеріледі, содан кейін typed normalizer, сәйкестендіру және review workflow жасалады, тек осы кезеңдерден кейін ғана RAW жазбаларын синхрондау қосылады. Бұл тәсіл `data.egov.kz` порталында жарияланған жаңа жинақтың trusted master data-ға автоматты түрде өтіп кетуіне жол бермейді.

GeoKZ жергілікті дерекқоры мен Core Dataset сыртқы сервистерсіз және `GEOKZ_EGOV_API_KEY` кілтінсіз де жұмысын жалғастырады.

## Қазіргі ресми каталог

Sync/process/review толық қолдайтын көздер:

- `kz-egov-oil-gas-fields` → `apiUri=stat_kgn_117`, бекітілген `v10`, `record_type=oil_gas_field`;
- `kz-egov-geological-study-licenses` → `apiUri=zher_koinauyn_geologiyalyk_zer2`, бекітілген `v6`, `record_type=geological_study_license`.

Геология комитетінің жаңа ресми кандидаттары:

- `kz-egov-solid-mineral-fields` → `apiUri=stat_kgn_118`, Қазақстан Республикасының қатты пайдалы қазбалары;
- `kz-egov-groundwater-fields` → `apiUri=stat_kgn_120`, Қазақстан Республикасының жерасты сулары кен орындары.

Ресми беттер:

```text
https://data.egov.kz/datasets/view?index=stat_kgn_118
https://data.egov.kz/datasets/view?index=stat_kgn_120
```

Бұл екі жинақ үшін GeoKZ белгісіз API нұсқасын ойдан шығармайды. Каталогта `LATEST_MAPPING` нұсқа саясаты көрсетіледі.

## `LATEST_MAPPING` нұсқа саясаты

Open Data Kazakhstan порталында dataset mapping-ті нұсқасын көрсетпей сұрауға болады. GeoKZ жарияланған нұсқаны анықтау үшін ресми endpoint қолданады:

```text
GET https://data.egov.kz/api/v4/mapping/{apiUri}
```

Connector тек `vN` пішіміндегі mapping кілттерін қабылдайды, мұндағы `N` — бүтін сан. Ең үлкен сандық нұсқа таңдалады, сондықтан `v10` нұсқасы `v2` нұсқасынан дұрыс түрде жаңа болып есептеледі. `preview` тәрізді басқа кілттер еленбейді. Табылған нұсқа connector өмірлік циклі ішінде кештеліп, metadata, mapping және data request үшін бірдей қолданылады.

Егер mapping ішінде `vN` түріндегі жарияланған нұсқа болмаса, операция `ExternalSourceProtocolError` қатесімен fail-closed режимінде тоқтайды. GeoKZ нұсқаны болжамайды және белгісіз endpoint-ке ауыспайды.

Тұрақтандырылған көздер үшін `PINNED` саясаты сақталады: `stat_kgn_117/v10` және `zher_koinauyn_geologiyalyk_zer2/v6` нақты тексерілген нұсқамен жұмыс істейді.

## Тіркеу және каталогты қарау

```text
POST /api/v1/integrations/kazakhstan/register
GET  /api/v1/integrations/kazakhstan/catalog?lang=kk
GET  /api/v1/integrations/kazakhstan/{code}/schema
```

`register` барлық белгілі ресми жинақ үшін жергілікті `ExternalDataSource` жазбасын жасайды. Бұл синхрондауға рұқсат берілді дегенді білдірмейді.

`stat_kgn_118` және `stat_kgn_120` үшін бастапқы күй әдейі қауіпсіз:

```text
enabled=false
sync_mode=MANUAL
version=LATEST_MAPPING
sync_supported=false
processing_supported=false
```

`source_config` ішінде `api_uri`, `record_type`, official/metadata/mapping/data URL templates, `version_policy`, `sync_supported` және `processing_supported` сақталады.

## Sync қосылмай тұрып schema inspection

Мына endpoint-тер:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/schema
GET /api/v1/integrations/kazakhstan/kz-egov-groundwater-fields/schema
```

алдымен mapping арқылы нақты жарияланған нұсқаны анықтайды, кейін versioned metadata және mapping алады. Бұл тексеру үшін eGov API key қажет емес. Жауап `LATEST_MAPPING` емес, анықталған нақты нұсқаны қайтарады.

Осылайша typed normalizer нақты ағымдағы schema бойынша жасалады. Open Data техникалық өріс атауларын өзгерте алатындықтан, normalizer жаңартылған сайын mapping қайта тексерілуі керек.

## Неліктен синхрондау әзірше жабық

Ресми dataset болуы автоматты импорт үшін жеткіліксіз. Жаңа `record_type` үшін sync қосылмай тұрып мыналар қажет:

1. нақты schema және identity strategy;
2. белгісіз немесе екіұшты schema-ны диагностикалайтын typed normalizer;
3. provenance сақтайтын normalized payload;
4. бар `GeologicalEntity` және alias объектілерімен match policy;
5. review queue және reviewer-locked шешімдер;
6. жаңа объектіні тек `DRAFT` ретінде жасау ережесі;
7. unit және PostgreSQL/PostGIS integration tests;
8. RU/KK/EN құжаттамасы.

Сондықтан:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-solid-mineral-fields/sync
```

қазіргі кезеңде басқарылатын configuration error қайтарады. Тіпті DB-дегі source қолмен enabled етілсе де, `ExternalConnectorRegistry` кодтағы `sync_supported=true` шарты орындалғанға дейін sync-ready connector бермейді.

`Update All` және scheduler де қауіпсіз: disabled source өткізіліп жіберіледі; DB-де күштеп enabled етілген catalog-only source `SKIPPED_UNSUPPORTED` күйін алады және RAW import басталмайды.

## API key

Metadata/mapping/schema inspection кілтсіз орындалады. API v4 арқылы нақты жазбаларды алу үшін жергілікті secret қажет:

```env
GEOKZ_EGOV_API_KEY=...
```

Кілт Git, құжаттама, log немесе desktop settings ішінде сақталмауы тиіс. PySide6 eGov key сақтамайды және GeoKZ API арқылы ғана жұмыс істейді.

## GeoKZ инварианттары

- upstream `apiUri` өзгертілмей сақталады;
- белгісіз нұсқа болжаммен алмастырылмайды;
- RAW және normalized payload бөлек сақталады;
- сыртқы дерек verified master data-ны үнсіз қайта жазбайды;
- `ExternalEntityLink=VERIFIED` дегеніміз `GeologicalEntity=VERIFIED` деген сөз емес;
- review арқылы жасалған жаңа геологиялық объект `DRAFT` күйінде қалады;
- upstream deletion master data-ны hard delete етпеуі тиіс;
- сыртқы сервис — optional enrichment layer, негізгі қолданбаның міндетті тәуелділігі емес.

## Келесі қадам

Осы catalog-only кезеңінен кейін бірінші толық pipeline `kz-egov-solid-mineral-fields` (`stat_kgn_118`) үшін іске асырылады: schema inspection → typed normalizer → matching/review → tests → содан кейін ғана `sync_supported=true`. Жерасты сулары `stat_kgn_120` бөлек келесі срезде орындалады, өйткені оның геологиялық semantics қатты пайдалы қазбалардан өзгеше.

Автор: **Sarmuldin Rinat — ura07srr@gmail.com**.
