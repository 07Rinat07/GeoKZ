# GeoKZ — корреляциялық қиманың UI/view-model contract-ы (KK)

## Мақсаты

Визуалды қима endpoint-і болашақ PySide6/web клиентіне арналған. Backend графиканы өзі салмайды, бірақ UI үшін дайын құрылымды қайтарады: ұңғыма колонкаларының реті, бірыңғай тереңдік шкаласы, реперлер, интервал жолақтары, корреляциялық сызықтар және үйлеспейтін деректер туралы ескертулер.

```text
POST /api/v1/correlation/wells/view
```

Request негізгі корреляциядағы сол `WellCorrelationRequest` contract-ын қолданады:

```json
{
  "reference_well_id": "UUID",
  "well_ids": ["UUID"],
  "language": "kk"
}
```

Қолданыстағы `POST /api/v1/correlation/wells` өзгермейді және analytical differences көзі болып қалады. View endpoint алдымен сол `WellCorrelationService` нәтижесін алады, кейін оны тек UI-ready contract-қа түрлендіреді. Сондықтан visual layer жаңа геологиялық интерпретация енгізбейді.

## Тереңдік шкаласы

`depth_axis` мыналарды береді:

- `depth_reference` — бүкіл қима үшін бір анық тереңдік жүйесі;
- `unit=m`;
- `direction=DOWN`;
- `min_depth_m`, `max_depth_m`;
- жоғарғы/төменгі visual margin үшін `padding_m`.

Depth reference детерминирленген басымдықпен таңдалады:

1. TVDSS;
2. TVD;
3. MD.

Алдымен already comparable marker/reservoir differences қаралады. Comparable pair болмаса, GeoKZ сол басымдық бойынша бірінші қолжетімді depth system-ді алады. Қауіпсіз render жасауға болатын дерек мүлде болмаса, техникалық TVDSS `0..1` шкаласы, `has_renderable_data=false` және `NO_RENDERABLE_DATA` warning қайтарылады.

GeoKZ trajectory дәлелінсіз интервалды MD-ден TVD/TVDSS-ке автоматты түрде өзгертпейді. Interval тек оның `depth_reference` мәні `depth_axis.depth_reference` мәнімен бірдей болса ғана шкалада көрсетіледі.

Marker үшін нақты `tvdss_m`, `true_vertical_depth_m` немесе `measured_depth_m` қолданылуы мүмкін. Қажетті alternative value жоқ болса, `depth_m` тек marker-дің өз `depth_reference` мәні таңдалған шкаламен сәйкес келгенде қолданылады.

## Ұңғыма колонкалары

`columns[]` request ретін сақтайды: бірінші reference well, одан кейін қайталанбайтын selected wells.

Әр колонкада:

- `column_index` — layout үшін тұрақты индекс;
- `well` — қолданыстағы `WellCard`;
- `is_reference`;
- `distance_from_reference_m`;
- `markers[]`;
- `intervals[]`.

Marker және interval ішінде `renderable` бар. Егер деректі ортақ depth scale-ға қауіпсіз қою мүмкін болмаса, `renderable=false`, scale coordinate `null`, ал бастапқы depth reference сақталады. Клиент мұндай элементтерді өзі қайта есептемеуі тиіс.

## Корреляциялық сызықтар

`correlation_lines[]` колонка индекстері және depth values арқылы сызық ұштарын дайын түрде береді.

Тұрақты `kind` мәндері:

```text
MARKER
HORIZON
```

`MARKER` тек таңдалған depth reference ішіндегі `MarkerDifference(comparable=true)` нәтижесінен жасалады.

`HORIZON` тек `ReservoirDifference(comparable_thickness=true)` үшін жасалып, салыстырылған interval жолақтарының midpoint нүктелерін байланыстырады. Бұл already matched interval pair-ды визуалды көрсету; жаңа автоматты стратиграфиялық шешім емес.

Әр line:

- `key` — `marker_code` немесе horizon атауы;
- `depth_reference`;
- `from_column_index`, `to_column_index`;
- `from_well_id`, `to_well_id`;
- `from_depth_m`, `to_depth_m`.

Сызықтар reference well-ге қатысты құрылады, өйткені қазіргі analytical correlation да reference-based. Клиент өз бетімен neighbour-to-neighbour жаңа байланыс жасамауы тиіс.

## Ескертулер

Тұрақты warning codes:

```text
DEPTH_REFERENCE_MISMATCH
NON_COMPARABLE_MARKERS
NON_COMPARABLE_INTERVALS
NO_RENDERABLE_DATA
NO_CORRELATION_LINES
```

`DEPTH_REFERENCE_MISMATCH` — ұңғыма деректерінің бір бөлігі response ішінде бар, бірақ ортақ шкалада көрсетілмейді.

`NON_COMPARABLE_MARKERS` және `NON_COMPARABLE_INTERVALS` HTTP error емес. GeoKZ салыстырылмайтын жағдайды scientific result ретінде сақтайды және жалған correlation line салмайды.

`NO_CORRELATION_LINES` — column/data render болуы мүмкін, бірақ байланыстыратын confirmed comparable pair жоқ дегенді білдіреді.

Warning мәтіні `language=ru|kk|en` бойынша локализацияланады; warning codes өзгермейтін client contract ретінде қолданылады.

## Интерпретация қауіпсіздігі

View-model verification status өзгертпейді, жаңа marker/interval құрмайды және fact жарияламайды. Ол existing correlation result-ты ғана визуалды contract-қа айналдырады.

Негізгі ережелер:

- TVDSS/TVD/MD үнсіз араластырылмайды;
- UNKNOWN depth reference compatible деп саналмайды;
- missing data айқын көрсетіледі;
- correlation line тек already comparable pair үшін бар;
- әр marker/interval `VerificationStatus` мәні сақталады;
- visual section expert geological interpretation-ды алмастырмайды.

## PySide6

Болашақ screen backend contract-ты тікелей қолдануы тиіс:

1. selected wells және reference well жіберу;
2. `depth_axis` бойынша vertical scale құру;
3. `column_index` бойынша columns орналастыру;
4. тек `renderable=true` элементтерді салу;
5. `correlation_lines` бойынша lines салу;
6. `warnings` және `policy_note` көрсету.

PySide6 depth-reference selection немесе correlation pairing алгоритмін өз ішінде қайталамауы тиіс.
