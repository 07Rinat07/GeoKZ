# GeoKZ — Documentation Policy / Құжаттама саясаты / Политика документации

## RU
Документация является частью Definition of Done. Любая пользовательская функция в том же pull request должна обновлять:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- контекстные подсказки `ru/kk/en`, если меняются поля, термины, предупреждения или workflow;
- архитектурные/предметные документы, если меняются модели данных или интеграции.

Функцию нельзя считать завершённой, если пользовательская инструкция существует только на одном языке. В документации необходимо явно различать: реализовано, в разработке, запланировано.

## KK
Құжаттама Definition of Done құрамына кіреді. Пайдаланушыға арналған әрбір өзгеріс сол pull request ішінде мыналарды жаңартуы тиіс:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- өрістер, терминдер, ескертулер немесе workflow өзгерген жағдайда `ru/kk/en` контекстік көмектер;
- деректер моделі немесе интеграциялар өзгерсе, архитектуралық/пәндік құжаттама.

Нұсқаулық тек бір тілде болса, функция аяқталды деп саналмайды. Құжаттамада іске асырылған, әзірленіп жатқан және жоспарланған функциялар нақты бөлінуі тиіс.

## EN
Documentation is part of the Definition of Done. Every user-facing feature change must update, in the same pull request:

- `docs/PROJECT_PLAN_V0_2.md`;
- `docs/USER_GUIDE_RU.md`;
- `docs/USER_GUIDE_KK.md`;
- `docs/USER_GUIDE_EN.md`;
- `ru/kk/en` contextual help when fields, terminology, warnings or workflows change;
- architecture/domain documentation when data models or integrations change.

A user-facing feature is not complete if its instructions exist in only one language. Documentation must clearly distinguish implemented, in-development and planned functionality.
