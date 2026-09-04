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
- контекстные подсказки `ru/kk/en`, если меняются поля, термины, предупреждения или workflow;
- архитектурные/предметные документы, если меняются модели данных или интеграции.

Функцию нельзя считать завершённой, если пользовательская инструкция или актуальный план отсутствуют хотя бы на одном из трёх языков. Для интеграций с авторизованными API также обязательна актуальная трёхъязычная инструкция по получению и безопасному хранению ключей. В документации необходимо явно различать: реализовано, в разработке, запланировано.

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
- өрістер, терминдер, ескертулер немесе workflow өзгерген жағдайда `ru/kk/en` контекстік көмектер;
- деректер моделі немесе интеграциялар өзгерсе, архитектуралық/пәндік құжаттама.

Пайдаланушы нұсқаулығы немесе өзекті жоспар үш тілдің кемінде бірінде жоқ болса, функция аяқталды деп саналмайды. Авторизацияланған API интеграциялары үшін API кілтін алу және қауіпсіз сақтау жөніндегі үштілді нұсқаулық та міндетті.

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
- `ru/kk/en` contextual help when fields, terminology, warnings or workflows change;
- architecture/domain documentation when data models or integrations change.

A user-facing feature is not complete if either the user instructions or the current roadmap are missing in any of the three supported languages. Integrations with authenticated APIs additionally require current trilingual instructions for obtaining and securely storing credentials.

Real secrets must never be placed in documentation. Examples may contain only empty values or explicit placeholders.
