# GeoKZ — пайдаланушы нұсқаулығы (KK)

Нұсқа: `0.2-dev`.

## Мақсаты
GeoKZ аумақ, кен орны, геологиялық құрылым және ұңғыма бойынша ақпаратты өз тексерілген базасынан және рұқсат етілген сыртқы дереккөздерден біріктіреді.

Негізгі жол: аумақ немесе координата → кен орындары/құрылымдар/ұңғымалар/сейсмика → объект паспорты → ұңғыма паспорты → интервалдар, литология, ҰГЗ, керн, сынақтар, мұнай/газ/су → көршілес ұңғымалар корреляциясы → дереккөз және дәлел.

## Тілдер
Интерфейс, анықтамалықтар, атаулар, кеңестер және пайдаланушы құжаттамасы қазақ, орыс және ағылшын тілдерінде қолжетімді.

## Координаттар бойынша іздеу
Географиялық енгізу: `43.652341 / 51.168420`. Үтір де қабылданады.

Проекциялық енгізу: `X=5085125.325`, `Y=711157.665`. `5085125,325 / 711157,665` пішімі де қабылданады.

Үлкен X/Y мәндері үшін бастапқы CRS көрсетіледі: EPSG, UTM аймағы, СК-42/Гаусс–Крюгер немесе кәсіпорынның жергілікті жүйесі. X/Y осьтерінің реті де таңдалады: X=Easting/Y=Northing немесе X=Northing/Y=Easting. GeoKZ CRS-ті тек сандар бойынша болжауға тиіс емес.

CRS көмекшісі Қазақстанның бойлық диапазонын қамтитын WGS84 және UTM 38N–45N нұсқаларын көрсетеді. Бойлық бойынша кеңес тек таңдауды тарылтады, бірақ бастапқы құжаттың CRS жүйесін растамайды. СК-42/Гаусс–Крюгер және кәсіпорынның жергілікті CRS жүйесі расталған EPSG/WKT/PROJ сипаттамасымен берілуі тиіс.

Енгізілген нүкте WGS84 жүйесіне түрлендірілгеннен кейін GeoKZ берілген радиуста әкімшілік контекстті, жақын геологиялық объектілерді, бұрғыланған ұңғымаларды олардың арақашықтығымен және интервалдарымен, сондай-ақ сейсмикалық зерттеулерді көрсетеді.

## Ұңғыма паспорты
Паспортта координаттар, түрі/операторы/мәртебесі, күндер, жалпы тереңдік, MD/TVD/TVDSS траекториясы, интервалдар, стратиграфия, литология, мұнай/газ/су, кеуектілік/өткізгіштік, ҰГЗ, сынақтар, дебиттер, қысым/температура, керн/үлгілер және құжаттар көрсетіледі.

## Көршілес ұңғымалардың корреляциясы
Координаттық іздеуден кейін пайдаланушы қажетті ұңғымаларды белгілеп, біреуін тірек ұңғыма ретінде таңдайды және корреляцияны іске қосады. GeoKZ реперлерді, литологияны, коллекторларды, мұнай/газ/суды, тереңдікті, қалыңдықты, net pay, кеуектілік пен өткізгіштікті визуалды және мәтіндік түрде салыстырады.

TVDSS басым қолданылады. Үйлеспейтін тереңдік жүйелері автоматты сызықпен байланыстырылмайды. Әр репердің дереккөзі, интерпретация әдісі және тексеру мәртебесі сақталады.

GeoKZ demo-наборындағы synthetic ұңғымалар тек интерфейс пен корреляцияны тексеруге арналған және өндірістік геологиялық факт болып саналмайды.

## Дереккөздер және жаңарту
Сыртқы деректер тексерілген GeoKZ мәндерін автоматты түрде ауыстырмайды. Алынған жазбалар алдымен RAW/staging қабатына түседі, кейін олар нормализациядан, GeoKZ объектілерімен сәйкестендіруден және сараптамалық тексеруден өте алады.

Қазіргі нұсқада Қазақстанның ресми ашық деректер порталы `data.egov.kz` API v4 арқылы қосылған. Екі геологиялық ресурс тіркелді:

1. `kz-egov-oil-gas-fields` — Қазақстан Республикасының мұнай-газ кен орындары (`apiUri=stat_kgn_117`, `v10`).
2. `kz-egov-geological-study-licenses` — жер қойнауын геологиялық зерттеу лицензиялары (`apiUri=zher_koinauyn_geologiyalyk_zer2`, `v6`).

GeoKZ ресми `apiUri` мен `version` мәндерін бөлек сақтайды. Ресурсты қоспас бұрын немесе version ауыстырғанда portal metadata және mapping арқылы field schema тексеріледі. RAW техникалық field атаулары өзгертілмейді, ал GeoKZ нормализацияланған атаулары бөлек жасалады.

Дереккөздер үшін автоматты жаңарту аралығы 168 сағат (аптасына бір рет) ретінде тіркеледі, сонымен бірге қолмен синхрондау кез келген уақытта орындалады.

### «Барлығын жаңарту» және жоспарлы sync

Барлық enabled source-ты қолмен жаңарту:

```text
POST /api/v1/integrations/sync-all
```

GeoKZ жалпы batch summary және әр source үшін жеке result қайтарады. Бір provider қатесі басқа source-тарды тоқтатпайды. Нәтижелерде `SUCCESS`, `FAILED`, `ALREADY_RUNNING`, `SKIPPED_DISABLED` және `SKIPPED_UNSUPPORTED` болуы мүмкін.

Scheduler күйі:

```text
GET /api/v1/integrations/scheduler/status
```

`next_due_at`, `due` және `running_run_id` болашақ PySide6 UI-ға source қашан қайта тексерілетінін және sync қазір орындалып жатқанын көрсетуге мүмкіндік береді.

Dedicated scheduler process тек due болған `AUTOMATIC` source-тарды орындайды:

```text
POST /api/v1/integrations/scheduler/run-due
```

Docker ішінде ол `geokz-external-sync-scheduler` service ретінде іске қосылады. FastAPI worker ішінде background loop жоқ. PostgreSQL row lock бір source үшін екі қатар `RUNNING` run ашылуына жол бермейді. Configurable timeout-тан ескі `RUNNING` `FAILED` күйіне ауысып, кейін жаңа sync іске қосылады.

`kz-egov-oil-gas-fields` синхрондалғаннан кейін `process` қадамын іске қосуға болады. GeoKZ кен орны атауын нормализациялап, бар `field` объектілері және олардың aliases бойынша сәйкестендіреді. Сәйкестік автоматты түрде verified болмайды: `REVIEW_REQUIRED` кандидаты жасалады. Бірнеше ықтимал сәйкестік және табылмаған жазбалар сараптамалық review үшін сақталады.

## Сыртқы кен орындарын сараптамалық тексеру
Техникалық review кезегі:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review
```

Пайдаланушы интерфейсі үшін локализацияланған view-model endpoint бар:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view?lang=kk&limit=100&offset=0
```

Бұл жауап pending жазбалардың жалпы санын, pagination күйін, локализацияланған entity атауын, `entity_verification_status`, candidates және backend дайындаған action descriptor-ларын (`CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`) береді. Әр action үшін `enabled`, `disabled_reason`, `required_fields`, `optional_fields` және нақты `path` қайтарылады, сондықтан PySide6/web клиенті backend business rules логикасын қайталамауы тиіс.

Пайдаланушы әр жазба үшін мына әрекеттердің бірін таңдай алады:

- ұсынылған байланысты растау;
- кандидаттан бас тарту және себеп жазу;
- жазбаны басқа бар `GeologicalEntity(object_type="field")` объектісімен қолмен байланыстыру;
- тек `matching.status=UNMATCHED` болса жаңа кен орнын жасау.

Байланысты растау `ExternalEntityLink` статусын `VERIFIED` етеді, бірақ `GeologicalEntity.verification_status` автоматты түрде өзгермейді. Жаңа объект жасалса, ол міндетті түрде `DRAFT` болып құрылады және кейін бөлек геологиялық тексеруден өтеді.

Негізгі review әрекеттері:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/confirm
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/links/{link_id}/reject
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/manual-link
POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/{record_id}/create-draft-field
```

Қайта `process` орындалғанда reviewer-locked шешімдер (`VERIFIED`, `REJECTED`, `MANUAL`, `verified_by` немесе review comment) үнсіз өзгертілмеуі тиіс.

## GeoKZ REST API

- `GET /api/v1/integrations/sources` — сыртқы source-тар және соңғы sync күйі;
- `GET /api/v1/integrations/scheduler/status` — scheduler due/running/error күйі;
- `POST /api/v1/integrations/sync-all` — қолмен «Барлығын жаңарту»;
- `POST /api/v1/integrations/scheduler/run-due` — scheduled due алгоритмін бір рет орындау;
- `GET /api/v1/integrations/kazakhstan/catalog` — ресми resources, `api_uri`, version және endpoint-тер;
- `GET /api/v1/integrations/kazakhstan/{code}/schema` — импортқа дейін ресми metadata және mapping алу;
- `POST /api/v1/integrations/kazakhstan/register` — ресурстарды жергілікті GeoKZ БД-сына тіркеу;
- `POST /api/v1/integrations/kazakhstan/{code}/sync` — таңдалған ресурсты қолмен синхрондау;
- `POST /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/process` — RAW кен орындарын нормализациялау және GeoKZ объектілерімен safe matching жасау;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review` — техникалық сараптамалық review кезегін көрсету;
- `GET /api/v1/integrations/kazakhstan/kz-egov-oil-gas-fields/review/view` — локализацияланған UI/view-model review queue contract алу.

Деректерді жүктеу үшін `data.egov.kz` developer API key талап етеді. Кілт тек `GEOKZ_EGOV_API_KEY` орта айнымалысында сақталады және Git репозиторийіне жазылмайды. Кілт болмаса да GeoKZ жергілікті базамен толық жұмыс істейді; scheduler нақты source қатесін жазып, process жұмысын жалғастырады.

Толық нұсқаулықтар:

- `docs/EXTERNAL_API_KEYS_KK.md` — API key алу және баптау;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md` — `apiUri`, mapping, endpoint, processing және GeoKZ resource naming ережелері;
- `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md` — confirm/reject/manual-link/create-draft-field review workflow;
- `docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md` — PySide6/web клиентіне арналған тұрақты review queue contract;
- `docs/EXTERNAL_SYNC_SCHEDULER_KK.md` — scheduler, Update All, due/retry және parallel-run protection.

## Көмектер мен кеңестер
Күрделі өрістер үшін қысқа кеңес, кеңейтілген түсіндірме, қадамдық шебер және диагностикалық ескерту қолданылады. CRS, X/Y реті, MD/TVD/TVDSS, ҰГЗ, корреляция және сыртқы дереккөздерді баптау үшін контекстік көмек міндетті.

Ағымдағы іске асыру мәртебесі: `docs/PROJECT_PLAN_V0_2_KK.md`.

## Визуалды корреляциялық қима
UI үшін бұрын есептелген корреляцияның үстінен backend-owned view-model қосылды; клиент геологиялық корреляцияны қайта есептемейді:

```text
POST /api/v1/correlation/wells/view
```

Backend ортақ depth scale-ды `TVDSS → TVD → MD` басымдығымен таңдайды. Таңдалған depth reference-ке қауіпсіз келмейтін реперлер мен интервалдар `renderable=false` болып қайтарылады және автоматты correlation line алмайды. `correlation_lines` ішінде `MARKER` және `HORIZON` сегменттері, ал `warnings` ішінде `DEPTH_REFERENCE_MISMATCH`, `NO_RENDERABLE_DATA`, `NO_CORRELATION_LINES` сияқты тұрақты diagnostic codes беріледі.

Клиент `VerificationStatus` пен warnings-ті көрсетуі тиіс, бірақ depth conversion немесе жаңа correlation link логикасын өз ішінде жасамауы керек. Толық контракт: `docs/CROSS_SECTION_VIEW_CONTRACT_KK.md`.
