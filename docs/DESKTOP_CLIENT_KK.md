# GeoKZ Desktop — PySide6 клиенті

GeoKZ Desktop — орталық GeoKZ HTTP API үстінде жұмыс істейтін Windows/desktop клиенті. Клиент **PostgreSQL-ге тікелей қосылмайды**, SQLAlchemy models импорттамайды және ғылыми верификация ережелерін өз ішінде қайталамайды. Review, provenance және business rules серверде қалады.

## Орнату

Desktop development үшін optional dependency орнатыңыз:

```powershell
python -m pip install -e ".[desktop]"
```

Backend бөлек іске қосылады, мысалы `http://127.0.0.1:8000`.

Іске қосу:

```powershell
geokz-desktop --api-url http://127.0.0.1:8000 --lang kk
```

немесе:

```powershell
python -m scripts.desktop --api-url http://127.0.0.1:8000 --lang kk
```

`ru`, `kk`, `en` тілдері қолдау табады.

## Кіру және session

Desktop мына endpoint-терді қолданады:

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Opaque bearer token тек process memory ішінде сақталады. Пароль немесе access token settings, log немесе файлға жазылмайды. Терезе жабылғанда logout орындалып, локал token state тазартылады.

Backend roles: `editor`, `expert`, `admin`. Клиент ағымдағы user және role көрсетеді, бірақ UI role check серверлік authorization орнына жүрмейді. Соңғы рұқсатты әрқашан backend тексереді.

## «Дереккөздер» экраны

Экран мына контракттарды біріктіреді:

```text
GET /api/v1/system/versions
GET /api/v1/about
GET /api/v1/core-dataset/status
GET /api/v1/integrations/sources
GET /api/v1/integrations/scheduler/status
```

Көрсетіледі:

- application version;
- Alembic/database schema revision;
- bundled Core Dataset version;
- installed Core Dataset version;
- provider/dataset version;
- due/running/error status;
- соңғы successful sync;
- соңғы source error.

«Барлығын жаңарту» батырмасы `POST /api/v1/integrations/sync-all` шақырады. External sync RAW/staging және sync history жаңартады, бірақ geological fact-ты VERIFIED етпейді және DRAFT/REVIEW_REQUIRED мәртебесін автоматты көтермейді.

## Мұнай-газ кен орындарын review

Queue тек backend-owned contract арқылы алынады:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view
```

Клиент `raw_payload`, `normalized_payload`, matching status, candidates және `entity_verification_status` көрсетеді.

Маңызды ереже: `ExternalEntityLink=VERIFIED` сыртқы ресми жазбамен байланыстың тексерілгенін білдіреді, бірақ **`GeologicalEntity=VERIFIED` дегенді білдірмейді**.

Әрекеттер backend action descriptors арқылы беріледі:

```text
CONFIRM_LINK
REJECT_LINK
MANUAL_LINK
CREATE_DRAFT_FIELD
```

Desktop business rules кестесін қайталамайды. Ол `enabled`, `disabled_reason`, `required_fields`, `optional_fields`, `method`, `path` мәндерін серверден оқиды. Disabled action клиенттен орындалмайды, ал сервер бәрібір соңғы authority болып қалады.

Desktop `reviewer` өрісін жібермейді. Reviewer identity authenticated session арқылы серверде анықталады, сондықтан UI жолы арқылы reviewer identity spoof жасауға болмайды.

## Лицензияларды review

Administrative license queue:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Шешімдер:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

`ACCEPTED` тек normalized administrative record RAW/upstream payload-пен салыстырылып тексерілгенін білдіреді. Бұл `ExternalEntityLink` жасамайды, `GeologicalEntity` жасамайды және geological fact жарияламайды.

## Provenance және аудит

Review экрандары RAW және normalized payload-ты қатар көрсетеді. Осылайша upstream source wording пен GeoKZ ішкі representation бірге көрінеді.

Master-data history үшін desktop мыналарды қолданады:

```text
GET /api/v1/audit/logs
GET /api/v1/audit/revisions/{resource_type}/{resource_id}
```

Толық `AuditLog` тек `admin` үшін қолжетімді. Revision history authenticated user-лерге `source`, `geological_entity`, `fact` resource types үшін беріледі.

Audit/revision history PostgreSQL деңгейінде append-only. Desktop оны өзгертуге немесе жоюға арналған API пайдаланбайды.

## UI асинхронды жұмысы

HTTP сұраулары `QThreadPool/QRunnable` арқылы орындалады және Qt event loop-ты блоктамайды. Network немесе HTTP API error қолданушыға нақты көрсетіледі. Қате болғанда клиент локалды scientific data-ны өзгертпейді және success нәтижесін болжамайды.

## Архитектуралық шекара

```text
PySide6 widgets
    ↓
GeoKZApiClient (httpx)
    ↓ HTTPS/HTTP
FastAPI application/use cases
    ↓
domain + repositories
    ↓
PostgreSQL/PostGIS
```

Тыйым салынған жол:

```text
PySide6 → SQLAlchemy model → PostgreSQL
```

Мұндай тікелей байланыс RBAC, AuditLog, revision history және backend-owned review contract-ты айналып өтеді.

## Тесттер

Desktop API client unit tests мынаны тексереді:

- bearer token login-нен кейін ғана жіберіледі;
- token memory-де ғана қалады;
- disabled action HTTP request жасамайды;
- action descriptor required fields алдын ала тексеріледі;
- server-owned action path локалды қайта құрастырылмайды;
- RU/KK/EN localization key set бірдей;
- HTTP `detail` error message ретінде сақталады.

`GET /api/v1/system/versions` PostgreSQL/PostGIS integration test нақты Alembic head және Core Dataset metadata-ны тексереді.

## Қазіргі шектеулер

Бірінші production-oriented desktop slice толық map, cross-section renderer, offline cache немесе Windows installer қоспайды. Қазір login/session, Data Sources, external review және provenance үшін қауіпсіз foundation жасалды. Келесі desktop кезеңдері Territory Explorer, Well Passport және correlation viewer-ді осы HTTP API архитектурасын сақтай отырып қоса алады.
