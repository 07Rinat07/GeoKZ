# GeoKZ — корреляциялық қиманың demo workflow нұсқаулығы (KK)

## Мақсаты

`POST /api/v1/correlation/demo/workflow` координатадан бастап дайын визуалды корреляциялық қимаға дейінгі қауіпсіз оқу сценарийін береді. Ол UX, API және болашақ PySide6/web-клиентті синтетикалық деректермен тексеруге арналған және өндірістік геологиялық факт көзі болып саналмайды.

Demo workflow жеке геологиялық алгоритм жасамайды. Ол GeoKZ-тің бар сервистерін оркестрациялайды:

1. `CoordinateResolver` бастапқы координатаны WGS84 жүйесіне қауіпсіз түрлендіреді;
2. `SpatialSearchService.search_nearby_wells()` PostGIS nearby search орындайды;
3. workflow тек ресми белгіленген demo dataset ұңғымаларын қалдырады;
4. пайдаланушы бір тірек және кемінде бір салыстырылатын ұңғыманы таңдайды;
5. `WellCrossSectionViewService` `POST /api/v1/correlation/wells/view` пайдаланатын сол backend-owned cross-section contract-ты құрады.

## Маңызды шектеу

`synthetic-correlation-demo-v1` dataset тек оқу үшін synthetic wells қамтиды. Response әрқашан `synthetic=true` және локализацияланған warning қайтарады. Бұл деректерді нақты кен орындары, қорлар, тереңдіктер, коллекторлар немесе сынақ нәтижелері туралы өндірістік ақпарат ретінде қолдануға болмайды.

Workflow кәдімгі production wells дәл сол search radius ішінде орналасса да оларды әдейі алып тастайды. Demo selection-ға тек demo dataset белгісі және ішкі demo well identifier бар жазбалар жіберіледі.

## 1-қадам — demo-ұңғымаларды іздеу

Сұрау мысалы:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "kk",
  "limit": 10
}
```

Endpoint:

```text
POST /api/v1/correlation/demo/workflow
```

Бірінші қадамда `reference_well_id` берілмейді, ал `well_ids` бос болады. Response:

```text
stage = DISCOVERY
```

Негізгі өрістер:

- `resolved_coordinate` — қауіпсіз түрлендірілген жұмыс WGS84 нүктесі;
- `nearby_demo_wells` — radius ішіндегі тек synthetic/demo ұңғымалар, distance бойынша сұрыпталған;
- `suggested_reference_well_id` — ең жақын demo well, UI ұсынысы ғана, геологиялық шешім емес;
- `can_build_cross_section` — кемінде екі demo well табылса `true`;
- `selection_contract` — келесі қадамның тұрақты backend contract-ы;
- `warning` — synthetic data туралы міндетті warning;
- `selection_note` — локализацияланған таңдау нұсқаулығы.

Әр `nearby_demo_wells` элементі `distance_m`, well card, белгілі intervals, `passport_path` және айқын `synthetic=true` береді.

## 2-қадам — таңдау және қима

Пайдаланушы ағымдағы `nearby_demo_wells` ішінен бір reference well және кемінде бір compared well таңдайды. Содан кейін сол endpoint қайта шақырылады:

```json
{
  "coordinate": {
    "type": "geographic",
    "latitude": 43.652341,
    "longitude": 51.168420
  },
  "radius_km": 5,
  "language": "kk",
  "limit": 10,
  "reference_well_id": "<reference demo well UUID>",
  "well_ids": [
    "<compared demo well UUID>"
  ]
}
```

Сәтті жауап:

```text
stage = CROSS_SECTION_READY
```

және қосымша мыналарды береді:

- `selection.reference_well_id`;
- `selection.compared_well_ids`;
- `cross_section` — толық `WellCrossSectionViewResponse`.

`cross_section` ортақ depth reference-ті `TVDSS → TVD → MD` басымдығымен таңдайды және `renderable`, `MARKER`/`HORIZON` lines, warnings, `VerificationStatus` өрістерін сақтайды. Demo workflow бұл ережелерді өзгерпейді.

## Таңдау қауіпсіздігі

Backend HTTP `422` қайтарады, егер:

- `reference_well_id` бар, бірақ `well_ids` бос болса;
- `well_ids` бар, бірақ `reference_well_id` жоқ болса;
- `well_ids` ішінде duplicate UUID болса;
- reference well бір уақытта `well_ids` ішінде болса;
- таңдалған well ағымдағы coordinate/radius бойынша табылған demo wells тізіміне кірмесе;
- coordinate немесе CRS қауіпсіз түрлендірілмесе.

Сондықтан клиент әртүрлі іздеу контексттері арасында demo UUID тізімін «сенімді» түрде өз бетімен тасымалдамауы тиіс. Әр қайталанған request ағымдағы coordinate/radius/limit және жергілікті БД бойынша қайта тексеріледі.

## Неліктен production wells кірмейді

Demo workflow UI-дың қайталанатын және қауіпсіз сынағын қамтамасыз етуі тиіс. Нақты ұңғыма demo coordinate маңында пайда болса, synthetic және production data араласпауы керек. Backend алдымен рұқсат етілген demo dataset well IDs анықтап, содан кейін PostGIS nearby query-ге тек сол UUID-лерді береді.

Қалыпты production workflow үшін жалпы endpoints пайдаланылады:

```text
POST /api/v1/spatial/nearby
POST /api/v1/correlation/wells/view
```

Demo endpoint оларды алмастырмайды.

## Demo dataset seed

Локалды synthetic dataset:

```text
python -m scripts.seed_correlation_demo
```

Қазіргі demo-наборда төрт well, `R1`/`R2` markers және `J-II` horizon бар. Dataset code `synthetic-correlation-demo-v1` ретінде орталықтандырылған, сондықтан seed script пен runtime workflow бір identifier қолданады.

Seed идемпотентті болуы тиіс: қайта іске қосылғанда demo entities, wells, markers немесе intervals duplicate жасалмайды.

## UI contract

PySide6/web-клиент үшін ұсынылған тәртіп:

1. coordinate және radius енгізу;
2. selection жоқ demo workflow шақыру;
3. тек `nearby_demo_wells` көрсету;
4. `suggested_reference_well_id` UI recommendation ретінде бөлек белгілеу;
5. бір reference well және 1–20 compared wells таңдауға мүмкіндік беру;
6. сол endpoint-ті selection арқылы қайта шақыру;
7. `cross_section` нәтижесін `docs/CROSS_SECTION_VIEW_CONTRACT_KK.md` бойынша көрсету;
8. synthetic warning-ті тұрақты көрсету.

Клиент production wells-ті demo selection-ға өз бетімен қоса алмайды, dataset marker-ді ауыстырмайды, PostGIS distance, depth conversion немесе correlation lines есептемейді.

## Тесттеу

Definition of Done нақты PostgreSQL/PostGIS integration test талап етеді. Test толық HTTP flow-ды тексереді: demo seed, дәл сол маңдағы бөлек production fixture well, discovery кезінде тек төрт demo well, TVDSS cross-section құру және production well таңдауға әрекет жасағанда `422` қайтару.

Осылайша test response serialization-ды ғана емес, synthetic demo мен кәдімгі GeoKZ деректерінің қауіпсіз шекарасын да тексереді.
