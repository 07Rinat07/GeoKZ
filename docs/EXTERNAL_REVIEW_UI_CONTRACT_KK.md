# GeoKZ — external review кезегінің UI/View-Model келісімшарты (KK)

Өзектілігі: 2026-09-04. Даму тармағы: `feature/external-review-ui-contract-v0.3`.

## Мақсаты

Бұл келісімшарт болашақ PySide6 клиентіне және басқа GeoKZ интерфейстеріне арналған. UI RAW payload құрылымын өздігінен талдамауы, review әрекеттерінің қолжетімділігін есептемеуі және confirm/reject/manual-link/create-draft-field URL жолдарын қолмен құрастырмауы тиіс. Backend дайын, типтелген және локализацияланған review queue view-model қайтарады.

Негізгі endpoint:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=kk&limit=100&offset=0
```

Қолдау көрсетілетін тілдер: `ru`, `kk`, `en`.

Төмен деңгейлі `GET .../review` endpoint кері үйлесімділік үшін сақталады. Пайдаланушы интерфейсі үшін `GET .../review/view` қолдану ұсынылады.

## Жоғарғы деңгейдегі жауап

View-model келесі өрістерді береді:

- `source_code` — дереккөздің тұрақты ішкі коды;
- `language` — локализация тілі;
- `title` — UI тақырыбы;
- `policy_note` — verification саясаты жөніндегі міндетті ескерту;
- `total_pending` — барлық `REVIEW_REQUIRED` жазбаларының саны;
- `returned_count` — ағымдағы беттегі жазбалар саны;
- `limit`, `offset` — pagination параметрлері;
- `has_more` — келесі бет бар-жоғы;
- `records` — review кезегінің жазбалары.

Мысал:

```json
{
  "source_code": "kz-egov-oil-gas-fields",
  "language": "kk",
  "title": "Сыртқы мұнай-газ кен орындарын сараптамалық тексеру",
  "total_pending": 42,
  "returned_count": 20,
  "limit": 20,
  "offset": 0,
  "has_more": true,
  "records": []
}
```

## Кезек жазбасы

Әр `records` элементі мыналарды қамтиды:

- `record_id` — GeoKZ ішіндегі external record UUID;
- `external_id` — upstream идентификаторы;
- `display_name` — UI үшін қауіпсіз атау;
- `status` — `ExternalRecord` мәртебесі;
- `matching_status` — нормализацияланған matching мәртебесі;
- `raw_payload` — upstream техникалық өрістері өзгертілмеген бастапқы жазба;
- `normalized_payload` — GeoKZ нормализацияланған интерпретациясы;
- `candidates` — қолданыстағы геологиялық объектілермен ықтимал байланыстар;
- `actions` — record деңгейіндегі әрекеттер.

Тұрақты `matching_status` мәндері:

```text
CANDIDATE
AMBIGUOUS
UNMATCHED
REVIEWER_LOCKED
UNAVAILABLE
UNKNOWN
```

`UNKNOWN` backend жаңа немесе бұрын белгісіз мәртебені кездестірген жағдайда қауіпсіз fallback ретінде пайдаланылады. Болашақ мәртебе үшін UI қате бермеуі тиіс.

## Байланыс кандидаты

Әр `candidates` элементінде:

- `link_id`;
- `entity_id`;
- `entity_display_name` — `kk/ru/en` fallback арқылы локализацияланған атау;
- `entity_verification_status` — геологиялық объектінің жеке verification мәртебесі;
- `match_method`;
- `match_confidence`;
- link `status`;
- бұрын шешім қабылданса, `verified_by` және `review_comment`;
- candidate деңгейіндегі `actions` болады.

Маңызды қағида: `ExternalEntityLink` мәртебесі мен `entity_verification_status` бір мағына емес. `ExternalEntityLink=VERIFIED` тек external record пен GeoKZ объектісінің сәйкестігін растайды. Ол объект координаттарын, қорларын, стратиграфиясын, литологиясын немесе басқа геологиялық қасиеттерін автоматты түрде VERIFIED етпейді.

## Action descriptor

UI әрекетті backend-тен дайын descriptor ретінде алады:

```json
{
  "code": "REJECT_LINK",
  "label": "Байланысты қабылдамау",
  "method": "POST",
  "path": "/api/v1/integrations/kazakhstan/.../reject",
  "enabled": true,
  "disabled_reason": null,
  "required_fields": ["reviewer", "comment"],
  "optional_fields": []
}
```

Тұрақты action code мәндері:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Клиент логика үшін `code`, экрандағы мәтін үшін `label`, backend берген нақты endpoint үшін `path`, батырма қолжетімділігі үшін `enabled`, ал форма құру үшін `required_fields` және `optional_fields` пайдалануы тиіс.

## Әрекеттердің қолжетімділігі

`CONFIRM_LINK` және `REJECT_LINK` тек unresolved automatic candidate (`REVIEW_REQUIRED` немесе `AUTO_MATCHED`) үшін қолжетімді. Reviewer шешімі бұрын бекітілсе, backend `enabled=false` және локализацияланған `disabled_reason` қайтарады.

`MANUAL_LINK` pending record үшін қолжетімді және `entity_id`, `reviewer` өрістерін талап етеді.

`CREATE_DRAFT_FIELD` тек `matching_status=UNMATCHED` жағдайында іске қосылады. Қалған мәртебелерде action descriptor сақталады, бірақ `enabled=false`. Осылайша бизнес-ереже PySide6 ішінде қайталанбайды.

External record негізінде жасалған жаңа геологиялық объект әрқашан `DRAFT` мәртебесінен басталады.

## Pagination

UI `limit` мәнін 1–200 аралығында және `offset >= 0` береді. Келесі бет:

```text
next_offset = offset + returned_count
```

формуласы бойынша сұралады және тек `has_more=true` болғанда жүктеледі.

`total_pending` backend жағында нақты `ExternalRecord(status=REVIEW_REQUIRED)` кезегі бойынша есептеледі; клиент оны ағымдағы беттің ұзындығынан есептемеуі тиіс.

## Ұсынылатын PySide6 flow

```text
External Review экранын ашу
  → GET review/view?lang=<ағымдағы тіл>
  → records/candidates көрсету
  → action descriptor-ларын көрсету
  → пайдаланушы әрекетті таңдайды
  → required/optional fields бойынша форма ашылады
  → POST action.path
  → сәтті жауаптан кейін review/view қайта жүктеледі
```

UI мыналарды жасамауы тиіс:

- match-ті автоматты түрде растау;
- VERIFIED link нәтижесінде geological entity мәртебесін VERIFIED ету;
- backend `path` берген кезде endpoint жолын қолмен жинау;
- `enabled=false` әрекетін орындау;
- review экранынан `policy_note` ескертуін алып тастау;
- RAW payload өзгерту.

## Үйлесімділік

Жаңа view-model бөлек endpoint ретінде енгізілді және бұрынғы `GET .../review` жауабының форматын өзгертпейді. Бұл PySide6/web UI енгізуді breaking change жасамай кезең-кезеңмен жүргізуге мүмкіндік береді.

Болашақта review басқа external resource түрлеріне кеңейтілсе, queue-level өрістер және action descriptor semantics сақталуы тиіс.

## Байланысты құжаттар

- `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`.
