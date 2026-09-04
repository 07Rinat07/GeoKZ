# GeoKZ — сыртқы кен орындарын тексеру және сәйкестендіру (KK)

Өзектілігі: 2026-09-04. Нұсқа: `0.2-dev`.

## Мақсаты

`kz-egov-oil-gas-fields` (`apiUri=stat_kgn_117`, `v10`) ресурсы синхрондалғаннан кейін GeoKZ жазбаларды RAW/staging қабатында сақтайды. `process` қадамы кен орны атауын нормализациялап, бар `GeologicalEntity(object_type="field")` объектілерімен ықтимал сәйкестікті ұсынады.

Атауы немесе alias бойынша автоматты match **сараптамалық растау емес**. Ол тек `ExternalEntityLink(status=REVIEW_REQUIRED)` жасайды.

## 1. Review queue алу

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Параметрлер: `limit` (1–200) және `offset`. Әр жазба үшін RAW payload, normalized payload, record status және ықтимал field links қайтарылады.

## 2. Ұсынылған байланысты растау

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
```

Мысал:

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Дереккөздер бойынша расталды"
}
```

Нәтиже: таңдалған link → `VERIFIED`, ExternalRecord → `ACCEPTED`, басқа аяқталмаған автоматты кандидаттар → `REJECTED`. Сыртқы API бар GeologicalEntity мәндерін автоматты түрде өзгертпейді.

## 3. Кандидатты қабылдамау

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
```

`reviewer` және `comment` міндетті. Бір кандидатты қабылдамау record-ты автоматты түрде жаппайды: ол manual link немесе қосымша review үшін қалады.

## 4. Бар кен орнымен қолмен байланыстыру

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
```

```json
{
  "entity_id": "GeologicalEntity UUID",
  "reviewer": "Sarmuldin Rinat",
  "comment": "Реестр атауы жұмыс атауынан өзгеше"
}
```

GeoKZ тек `object_type=field` объектісімен байланыстыруға рұқсат береді. Link `match_method=MANUAL`, `status=VERIFIED` болады, бірақ GeologicalEntity өзінің бұрынғы `verification_status` мәнін сақтайды.

## 5. UNMATCHED жазбасынан жаңа field жасау

Тек `matching.status=UNMATCHED` болса:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

```json
{
  "reviewer": "Sarmuldin Rinat",
  "comment": "Кейінгі геологиялық тексеру үшін карточка жасау",
  "name_ru": "Название",
  "name_kk": "Атауы",
  "name_en": "Name"
}
```

Маңызды қағида: жаңа `GeologicalEntity` **тек `DRAFT`** мәртебесімен жасалады. Ресми registry record-пен link расталғаны объектінің геологиясы, координаттары, стратиграфиясы, ұңғымалары немесе қорлары тексерілді дегенді білдірмейді. Олар бөлек evidence және expert review арқылы расталады.

`geological_context` ішінде source provenance, external record UUID және upstream external id сақталады.

## 6. Сарапшы шешімін қорғау

`VERIFIED`/`REJECTED`, `MANUAL`, `verified_by` немесе review comment бар link reviewer-locked болып есептеледі. Кейінгі sync/process оны үнсіз өзгерте алмайды. Upstream атауы өзгерсе, тек аяқталмаған автоматты `REVIEW_REQUIRED` links қайта есептеледі.

## 7. v0.2-dev шектеуі

Толық authentication және AuditLog әлі жоқ, сондықтан `reviewer` request body ішінде беріледі. Production нұсқасында ол авторизацияланған user identity-мен алмастырылады және барлық review actions audit/revision history ішінде сақталады.

## 8. Ұсынылатын workflow

```text
register → schema → sync → process → review queue
  → confirm / reject / manual link / create DRAFT
  → геологиялық тексеру
  → кейін ғана VERIFIED master data
```

Байланысты құжаттар: `KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`, `EXTERNAL_API_KEYS_KK.md`, `USER_GUIDE_KK.md`, `PROJECT_PLAN_V0_2_KK.md`.
