# GeoKZ — Documentation Policy / Құжаттама саясаты / Политика документации

## RU
Документация является частью Definition of Done. Любая пользовательская функция в том же pull request должна обновлять:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`;
- `docs/PROJECT_PLAN_V0_2_EN.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- `docs/EXTERNAL_API_KEYS_RU.md`, `docs/EXTERNAL_API_KEYS_KK.md`, `docs/EXTERNAL_API_KEYS_EN.md`, если меняются внешние API, ключи, секреты или порядок настройки интеграций;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`, если меняются Kazakhstan Open Data API, `apiUri`, версии, mapping, naming conventions, endpoints или правила подключения ресурсов;
- `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`, если меняются normalization/matching/review, статусы связей или правила создания DRAFT-объектов из внешних записей;
- `docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md`, если меняется UI/view-model contract очереди review, action codes, action availability, pagination или формы действий;
- `docs/EXTERNAL_SYNC_SCHEDULER_RU.md`, `docs/EXTERNAL_SYNC_SCHEDULER_KK.md`, `docs/EXTERNAL_SYNC_SCHEDULER_EN.md`, если меняются scheduler, Update All, due/retry, parallel-run protection или per-source sync status;
- контекстные подсказки `ru/kk/en`, если меняются поля, термины, предупреждения или workflow;
- архитектурные/предметные документы, если меняются модели данных или интеграции.

Функцию нельзя считать завершённой, если пользовательская инструкция или актуальный план отсутствуют хотя бы на одном из трёх языков. Для интеграций с авторизованными API также обязательна актуальная трёхъязычная инструкция по получению и безопасному хранению ключей. Для внешних каталогов ресурсов отдельно документируются официальный идентификатор ресурса, версия, схема полей и правила внутреннего именования GeoKZ. Для review-функций обязательно различать статус связи с источником и статус верификации самого геологического объекта: подтверждённый `ExternalEntityLink` не должен автоматически превращать новый объект в `VERIFIED`. UI не должен дублировать backend business rules: доступность действий и обязательные поля передаются через стабильный action descriptor. Scheduler не должен запускаться как background loop внутри каждого FastAPI worker; для периодического sync используется отдельный process/service и PostgreSQL-защита от параллельного run.

Реальные секреты запрещено включать в документацию. В примерах допускаются только пустые значения или явные placeholders, например `GEOKZ_EGOV_API_KEY=ВАШ_РЕАЛЬНЫЙ_КЛЮЧ`.

## KK
Құжаттама Definition of Done құрамына кіреді. Пайдаланушыға арналған әрбір өзгеріс сол pull request ішінде мыналарды жаңартуы тиіс:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`;
- `docs/PROJECT_PLAN_V0_2_EN.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- сыртқы API, API кілттері, secrets немесе integration setup өзгерсе, `docs/EXTERNAL_API_KEYS_RU.md`, `docs/EXTERNAL_API_KEYS_KK.md`, `docs/EXTERNAL_API_KEYS_EN.md`;
- Kazakhstan Open Data API, `apiUri`, version, mapping, naming conventions, endpoints немесе ресурс қосу ережелері өзгерсе, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md`;
- normalization/matching/review, link status немесе сыртқы жазбадан DRAFT объект жасау ережесі өзгерсе, `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md`;
- review queue UI/view-model contract, action codes, action availability, pagination немесе action form өзгерсе, `docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md`;
- scheduler, Update All, due/retry, parallel-run protection немесе per-source sync status өзгерсе, `docs/EXTERNAL_SYNC_SCHEDULER_RU.md`, `docs/EXTERNAL_SYNC_SCHEDULER_KK.md`, `docs/EXTERNAL_SYNC_SCHEDULER_EN.md`;
- өрістер, терминдер, ескертулер немесе workflow өзгерген жағдайда `ru/kk/en` контекстік көмектер;
- деректер моделі немесе интеграциялар өзгерсе, архитектуралық/пәндік құжаттама.

Пайдаланушы нұсқаулығы немесе өзекті жоспар үш тілдің кемінде бірінде жоқ болса, функция аяқталды деп саналмайды. Авторизацияланған API интеграциялары үшін API кілтін алу және қауіпсіз сақтау жөніндегі үштілді нұсқаулық та міндетті. Сыртқы ресурс каталогтары үшін ресми ресурс идентификаторы, нұсқасы, field schema және GeoKZ ішкі naming rules бөлек құжатталады. Review құжаттамасы source link мәртебесін геологиялық объектінің verification status мәнінен нақты ажыратуы тиіс: verified ExternalEntityLink жаңа объектіні автоматты түрде VERIFIED етпейді. UI backend business rules ережелерін қайталамауы керек; action availability және required fields backend action descriptor арқылы беріледі. Periodic scheduler әр FastAPI worker ішінде background loop ретінде іске қосылмайды; dedicated process/service және PostgreSQL parallel-run protection қолданылады.

Нақты secrets құжаттамаға енгізілмейді. Мысалдарда тек бос мәндер немесе айқын placeholders қолданылады.

## EN
Documentation is part of the Definition of Done. Every user-facing feature change must update, in the same pull request:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/PROJECT_PLAN_V0_2_KK.md`;
- `docs/PROJECT_PLAN_V0_2_EN.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- `docs/EXTERNAL_API_KEYS_RU.md`, `docs/EXTERNAL_API_KEYS_KK.md`, and `docs/EXTERNAL_API_KEYS_EN.md` when external APIs, credentials, secrets or integration setup change;
- `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_RU.md`, `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_KK.md`, and `docs/KAZAKHSTAN_OPEN_DATA_INTEGRATION_EN.md` when Kazakhstan Open Data API, `apiUri`, versions, mappings, naming conventions, endpoints or resource onboarding rules change;
- `docs/KAZAKHSTAN_FIELD_REVIEW_RU.md`, `docs/KAZAKHSTAN_FIELD_REVIEW_KK.md`, and `docs/KAZAKHSTAN_FIELD_REVIEW_EN.md` when normalization/matching/review, link statuses, or DRAFT creation rules change;
- `docs/EXTERNAL_REVIEW_UI_CONTRACT_RU.md`, `docs/EXTERNAL_REVIEW_UI_CONTRACT_KK.md`, and `docs/EXTERNAL_REVIEW_UI_CONTRACT_EN.md` when the review queue UI/view-model contract, action codes, action availability, pagination or action forms change;
- `docs/EXTERNAL_SYNC_SCHEDULER_RU.md`, `docs/EXTERNAL_SYNC_SCHEDULER_KK.md`, and `docs/EXTERNAL_SYNC_SCHEDULER_EN.md` when scheduler behavior, Update All, due/retry policy, parallel-run protection or per-source sync status changes;
- `ru/kk/en` contextual help when fields, terminology, warnings or workflows change;
- architecture/domain documentation when data models or integrations change.

A user-facing feature is not complete if either the user instructions or the current roadmap are missing in any of the three supported languages. Integrations with authenticated APIs additionally require current trilingual instructions for obtaining and securely storing credentials. External resource catalogs must separately document the upstream resource identifier, version, field schema and GeoKZ internal naming rules. Review documentation must clearly separate source-link verification from geological-object verification: a verified `ExternalEntityLink` must never automatically make a newly created geological object `VERIFIED`. A client must not duplicate backend business rules; action availability and form requirements are exposed through stable action descriptors. The periodic scheduler must not run as a background loop inside every FastAPI worker; use a dedicated process/service and PostgreSQL parallel-run protection.

Real secrets must never be placed in documentation. Examples may contain only empty values or explicit placeholders.
