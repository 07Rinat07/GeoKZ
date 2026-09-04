# GeoKZ — Kazakhstan Open Data / data.egov.kz интеграциясы (KK)

Өзектілігі: 2026-09-04.

## 1. data.egov.kz ресми терминологиясы

GeoKZ портал терминдерін өзгертпей қолданады:

- `apiUri` — `data.egov.kz` жүйесіндегі dataset-тің техникалық индексі/идентификаторы;
- `version` — ресурс нұсқасы, мысалы `v10`;
- `fields` — dataset өрістерінің техникалық атаулары;
- `labelRu`, `labelKk`, `labelEn` — metadata ішіндегі пайдаланушыға көрсетілетін атаулар;
- `source` — API v4 сұрауының JSON-параметрі; онда `from`, `size`, `query`, `sort` және Elasticsearch іздеу параметрлері беріледі.

GeoKZ ресурс мысалы:

```text
GeoKZ code:  kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

`GeoKZ code` — connector үшін біздің тұрақты идентификатор. Ол ресми `apiUri` мәнін алмастырмайды және өзгертпейді.

## 2. Ресми REST үлгілері

`{apiUri}` және `{version}` үшін:

```text
Metadata:
GET https://data.egov.kz/meta/{apiUri}/{version}

Mapping / өрістер құрылымы:
GET https://data.egov.kz/api/v4/mapping/{apiUri}/{version}

API v4 деректері:
GET https://data.egov.kz/api/v4/{apiUri}/{version}?source={JSON}

Detailed API:
GET https://data.egov.kz/api/detailed/{apiUri}/{version}?source={JSON}
```

Нақты деректерді алу кезінде GeoKZ портал талаптарына сәйкес пайдаланушының API key мәнін жібереді. Кілт тек `GEOKZ_EGOV_API_KEY` арқылы сақталады.

Ресми API сипаттамасы: `https://data.egov.kz/pages/samples`.

## 3. GeoKZ сыртқы ресурстарды қалай атайды

### 3.1 `code`

GeoKZ ішкі тұрақты slug:

```text
kz-egov-<domain>
```

Мысалдар:

```text
kz-egov-oil-gas-fields
kz-egov-geological-study-licenses
```

Ережелер:

- lowercase;
- ASCII;
- kebab-case;
- `data.egov.kz` үшін `kz-egov-` префиксі;
- ресурс мағынасын білдіреді;
- нұсқа `code` ішіне кірмейді.

### 3.2 `api_uri`

Порталдың ресми `apiUri` мәні өзгеріссіз сақталады:

```text
stat_kgn_117
zher_koinauyn_geologiyalyk_zer2
```

Оны аударуға, қысқартуға немесе GeoKZ атауымен алмастыруға болмайды.

### 3.3 `version`

Бөлек және өзгеріссіз сақталады:

```text
v10
v6
```

### 3.4 `record_type`

GeoKZ нормализацияланған бір жазба түрі:

```text
oil_gas_field
geological_study_license
```

Ережелер:

- ағылшын тілі;
- lowercase;
- singular;
- snake_case;
- бір жазбаның мәнін сипаттайды.

### 3.5 RAW өрістері

`data.egov.kz`-тен келген техникалық field атаулары `raw_payload` ішінде өзгеріссіз сақталады. GeoKZ нормализацияланған өрістері бөлек `normalized_payload` немесе domain model ішінде жасалады.

## 4. Жаңа ресурсты дұрыс қосу реті

1. `data.egov.kz` порталынан ресми dataset табу.
2. Оның `apiUri` және өзекті `version` мәндерін алу.
3. Metadata тексеру:

```text
GET /meta/{apiUri}/{version}
```

4. Mapping тексеру:

```text
GET /api/v4/mapping/{apiUri}/{version}
```

5. Техникалық field атаулары мен типтерін салыстыру.
6. `source={"size":5}` тәрізді шағын тест сұрауын орындау.
7. Тұрақты identity field таңдау; field атауы өзгеруі мүмкін болса alias group көрсету.
8. Ресурсты `app/integrations/kazakhstan_open_data.py` файлына қосу.
9. RU/KK/EN атаулары мен сипаттамаларын қосу.
10. Registry, metadata/mapping және parsing tests қосу.
11. License/terms және attribution тексеру.
12. Ресурсты GeoKZ БД-сына тіркеу.
13. Алғашқы синхрондауды тек RAW/staging қабатына орындау.
14. Тексерілгеннен кейін normalization/matching/review іске асыру.

## 5. GeoKZ арқылы ресурсты тексеру

Каталог:

```text
GET /api/v1/integrations/kazakhstan/catalog
```

GeoKZ әр ресурс үшін мыналарды қайтарады:

- `code`;
- `api_uri`;
- `version`;
- `record_type`;
- `metadata_url`;
- `mapping_url`;
- `data_url_template`;
- `detailed_url_template`;
- API key конфигурация күйі;
- тіркелу күйі.

Жүктемес бұрын ресми schema/mapping тексеру:

```text
GET /api/v1/integrations/kazakhstan/{code}/schema
```

Жауап:

```text
code
api_uri
version
metadata
mapping
```

Бұл endpoint деректерді нормализацияламайды немесе жарияламайды; ол сыртқы ресурс контрактын тексеруге арналған.

## 6. Тіркеу және синхрондау

Белгілі ресурстарды тіркеу:

```text
POST /api/v1/integrations/kazakhstan/register
```

Қолмен синхрондау:

```text
POST /api/v1/integrations/kazakhstan/{code}/sync
```

Деректер ағыны:

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

## 7. Қазір қосылған ресурстар

### Қазақстан Республикасының мұнай-газ кен орындары

```text
code:        kz-egov-oil-gas-fields
apiUri:      stat_kgn_117
version:     v10
record_type: oil_gas_field
```

### Жер қойнауын геологиялық зерттеуге берілген лицензиялар

```text
code:        kz-egov-geological-study-licenses
apiUri:      zher_koinauyn_geologiyalyk_zer2
version:     v6
record_type: geological_study_license
```

## 8. Үйлесімділік ережесі

Портал жаңа `v11` нұсқасын шығарса, GeoKZ `code` мәнін өзгертпейді. `version`, endpoint-тер және қажет болса normalization mapping жаңартылады. Нұсқаны ауыстырмас бұрын metadata/mapping салыстырылып, contract tests орындалады.

## 9. Байланысты құжаттар

- `docs/EXTERNAL_API_KEYS_KK.md` — API key алу және қауіпсіз сақтау;
- `docs/USER_GUIDE_KK.md` — сыртқы дереккөздермен жұмыс;
- `docs/PROJECT_PLAN_V0_2_KK.md` — өзекті roadmap;
- `docs/DOCUMENTATION_POLICY.md` — RU/KK/EN құжаттамасын синхронды жаңарту ережесі.

## 10. Мұнай-газ кен орындарын нормализациялау және matching

`kz-egov-oil-gas-fields` үшін RAW синхрондаудан кейінгі processing endpoint іске асырылды:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process
```

GeoKZ осы dataset нақты беретін деректі ғана нормализациялайды — кен орнының атауын. RAW payload өзгеріссіз сақталады. Нормализацияланған payload ішінде `entity_type=field`, `name_ru`, matching key және бастапқы field атауы сақталады.

Matching бар `GeologicalEntity(object_type="field")` объектілерімен және `EntityName` aliases арқылы орындалады. Регистр, типографиялық тырнақшалар, артық бос орындар және `ё/е` айырмасы салыстыру үшін нормализацияланады, бірақ upstream бастапқы мәні өзгертілмейді.

Қауіпсіздік ережелері:

- exact name match тек `ExternalEntityLink(status=REVIEW_REQUIRED)` жасайды;
- alias match те review талап етеді;
- бірнеше кандидат `AMBIGUOUS` ретінде белгіленеді;
- кандидат жоқ болса `UNMATCHED` болады;
- адам бұрын `VERIFIED` немесе `REJECTED` еткен link reviewer-locked және автоматты түрде өзгертілмейді;
- сыртқы dataset жаңа verified `GeologicalEntity` объектісін автоматты түрде жасамайды немесе жарияламайды.

Endpoint жауабында `processed`, `normalized`, `exact_matches`, `alias_matches`, `ambiguous`, `unmatched`, `normalization_errors`, `reviewer_locked` санағыштары беріледі.
