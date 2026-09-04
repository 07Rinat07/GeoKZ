# GeoKZ — жергілікті және ұйымдық CRS тізілімі

## Мақсаты

GeoKZ өндірістік X/Y координаттары үшін ұйымның расталған координат жүйелерін тұрақты сақтайды. Бұл бастапқы материалдар СК-42/Гаусс–Крюгерді, кәсіпорынның жергілікті торын, арнайы проекцияны немесе сандардың өзінен қауіпсіз анықтауға болмайтын басқа CRS қолданған кезде қажет.

Негізгі қағида: GeoKZ **CRS пен осьтер ретін болжамайды**. Жергілікті жүйені қолданар алдында нақты `EPSG`, `WKT` немесе `PROJ` анықтамасы, бастапқы дереккөзге сілтеме және айқын растау болуы тиіс.

## Деректер моделі

`20260904_0005` миграциясы `organization_crs_definitions` кестесін қосады. Әр жазбада:

- тұрақты `code`;
- RU/KK/EN атаулары;
- `definition_kind`: `EPSG`, `WKT` немесе `PROJ`;
- бастапқы `definition`;
- нормализацияланған `canonical_wkt`;
- PROJ анықтай алса authority name/code;
- `default_axis_order`;
- `source_reference`;
- notes;
- `is_confirmed`, `confirmed_by`, `confirmed_at`, `confirmation_note`;
- `is_active` және timestamps сақталады.

`confirmed_by` қазір request арқылы берілетін reviewer identifier. Authenticated user және толық AuditLog кейін бөлек енгізіледі; сондықтан қазіргі confirm — техникалық workflow, корпоративтік access control орнына жүрмейді.

## Өмірлік цикл

1. CRS расталмаған жазба ретінде жасалады.
2. Backend анықтаманы pyproj/PROJ арқылы тексереді және оның projected CRS екенін растайды.
3. Бастапқы definition және canonical WKT сақталады.
4. Маман `source_reference`, definition және `axis_order` мәндерін координат паспорты, геодезиялық құжаттама, жоба немесе ресми сипаттамамен салыстырады.
5. Жеке confirm әрекеті орындалады.
6. Тек active және `is_confirmed=true` жазба `selectable` болады және `registered_crs_code` арқылы қолданылады.

Definition, definition kind, `default_axis_order` немесе `source_reference` өзгерсе, GeoKZ confirmation күйін автоматты түрде алып тастайды. CRS қайта тексеріліп, қайта расталуы тиіс.

## REST API

Барлық жазбалар:

```text
GET /api/v1/spatial/crs-definitions?lang=kk
```

Тек таңдауға болатындары:

```text
GET /api/v1/spatial/crs-definitions?lang=kk&selectable_only=true
```

Жасау:

```text
POST /api/v1/spatial/crs-definitions?lang=kk
```

```json
{
  "code": "company-grid-01",
  "name_ru": "Локальная сетка предприятия 01",
  "name_kk": "Кәсіпорынның жергілікті торы 01",
  "name_en": "Company local grid 01",
  "definition_kind": "EPSG",
  "definition": "EPSG:32639",
  "default_axis_order": "x_easting_y_northing",
  "source_reference": "Жобаның координат жүйесі паспорты № ..."
}
```

Өзгерту:

```text
PATCH /api/v1/spatial/crs-definitions/{definition_id}?lang=kk
```

Растау:

```text
POST /api/v1/spatial/crs-definitions/{definition_id}/confirm?lang=kk
```

```json
{
  "confirmed_by": "geodesy-reviewer",
  "confirmation_note": "Координат паспортымен салыстырылды"
}
```

## Координаттық іздеуде қолдану

Расталғаннан кейін ұзын WKT/PROJ орнына тұрақты `registered_crs_code` беріледі:

```json
{
  "coordinate": {
    "type": "projected",
    "x": 711157.665,
    "y": 4851250.325,
    "registered_crs_code": "company-grid-01"
  },
  "radius_km": 5,
  "language": "kk",
  "limit": 25
}
```

Backend расталған definition мен расталған `axis_order` мәнін жүктейді, нүктені WGS84 жүйесіне түрлендіреді және `resolved_coordinate` ішінде `registered_crs_code` қайтарады. Клиент әр request ішінде CRS анықтамасын қайталауға тиіс емес.

Тікелей енгізу үшін `crs` өрісі әлі де қолжетімді, бірақ бұл жағдайда `axis_order` міндетті. `crs` және `registered_crs_code` мәндерін бір уақытта беруге болмайды.

## Қателер және қауіпсіздік

- `404` — registry code табылмады;
- `409` — жазба бар, бірақ расталмаған немесе inactive;
- `422` — definition PROJ/pyproj арқылы оқылмайды, өндірістік X/Y үшін geographic CRS берілген, client axis order расталған мәнге қайшы немесе coordinate payload қате.

СК-42/Гаусс–Крюгерді тек «СК-42» атауымен тіркеуге болмайды. Расталған дереккөзден zone/projection/datum нақты сипаттамасы қажет. Кәсіпорынның local CRS жүйесіне де осы қағида қолданылады: атау немесе ұқсас сан диапазоны CRS дәлелі емес.

## Инварианттар

- `source_reference` міндетті;
- `axis_order` расталған CRS анықтамасының бөлігі;
- расталмаған жазба координат түрлендіруге қатыспайды;
- critical field өзгерсе `is_confirmed` алынады;
- reproducibility үшін canonical WKT сақталады;
- local CRS бастапқы X/Y және provenance мәндерін жоғалтпайды;
- UI confirmation status көрсетуі және unconfirmed жазбаларды selectable ретінде ұсынбауы тиіс.
