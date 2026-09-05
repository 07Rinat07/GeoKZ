# GeoKZ Core Dataset — KK

## Мақсаты

GeoKZ Core Dataset — қолданбамен бірге жеткізілетін және Alembic schema migration-дарынан бөлек PostgreSQL/PostGIS-ке орнатылатын тәуелсіз нұсқаланатын базалық деректер жинағы.

Нұсқалар әдейі бөлінеді:

- GeoKZ қолданба нұсқасы;
- Alembic revision / дерекқор схемасы;
- GeoKZ Core Dataset нұсқасы;
- сыртқы provider нұсқалары мен checkpoints.

Контентті жаңарту Alembic data migration талап етпеуі тиіс.

## Ағымдағы bundled snapshot

```text
dataset_code:    geokz-core
dataset_version: 2026.09.0-bootstrap
schema_version:  1
namespace:       geokz-core:
```

Алғашқы bootstrap әдейі минималды: ішкі metadata source жазбасы және шекара/геометрияны бекітпейтін «Қазақстан Республикасы» country-level navigation жазбасы бар. `entities.jsonl` және `facts.jsonl` әзірше бос. GeoKZ baseline толтыру үшін ойдан шығарылған геологиялық фактілерді қоспайды.

`geokz-core:source:bootstrap` — Core Dataset техникалық metadata жазбасы, геологиялық evidence source емес.

## Manifest және файлдар

Bundle `data/bootstrap/core_dataset/` ішінде:

```text
manifest.json
sources.jsonl
regions.geojson
entities.jsonl
facts.jsonl
```

`manifest.json` dataset нұсқасын, `schema_version`, namespace, dependencies және әр файлдың SHA-256 мәнін сақтайды. Required файл bundle root ішінде болуы тиіс; absolute path және `..` қабылданбайды.

Дерекқорға жазбас бұрын GeoKZ мыналарды тексереді:

1. manifest JSON/Pydantic schema;
2. қолдау көрсетілетін `schema_version`;
3. duplicate file path/kind болмауы;
4. path traversal болмауы;
5. required файлдардың болуы;
6. әр файлдың SHA-256 мәні;
7. payload түрлері;
8. әр тип ішінде `external_id` бірегейлігі;
9. міндетті `geokz-core:` namespace;
10. bundle ішіндегі parent/source/entity/related facts сілтемелері.

Schema v1-де `minimum_app_version` көрсетуге және болашақ compatibility policy-ге арналған metadata. Қазір semantic-version бойынша қатаң gate орындалмайды; v1 нақты compatibility gate — `schema_version`.

## Transaction және rollback

Importer бір bundle-дің барлық upsert операцияларын бір SQLAlchemy transaction ішінде орындайды. `CoreDatasetState` тек сәтті импорттың соңында жазылады. Exception кезінде rollback орындалады, сондықтан жартылай орнатылған baseline жарамды күй болып саналмайды.

Бір manifest SHA-256 қайта орнатылса, операция idempotent: importer `changed=false` қайтарады және duplicate жазбалар жасамайды.

Core Dataset жеке `geokz-core:` namespace қолданады. Бұл baseline жазбаларын пайдаланушы, сыртқы және сарапшы тексерген объектілерден бөледі. Қазіргі importer arbitrary name match арқылы existing master data-ны қайта жазуға рұқсат бермейді.

## REST API

Bundled және installed version күйі:

```text
GET /api/v1/core-dataset/status
```

Жауапта `bundled_version`, `schema_version`, manifest SHA-256, dependencies, installed state және `update_available` бар.

Жазбасыз тексеру:

```text
POST /api/v1/core-dataset/install?dry_run=true&lang=kk
```

Bundled snapshot орнату:

```text
POST /api/v1/core-dataset/install?lang=kk
```

HTTP endpoint arbitrary manifest path қабылдамайды: сервер тек trusted bundled snapshot орнатады. Local bundle әкімшілік диагностикасы үшін CLI қолданылады.

## CLI

```text
python -m scripts.core_dataset validate
python -m scripts.core_dataset install --dry-run
python -m scripts.core_dataset install
python -m scripts.core_dataset status
```

Local диагностика кезінде CLI positional argument ретінде `manifest.json` нақты жолын да қабылдайды.

## About

`GET /api/v1/about` бөлек көрсетеді:

```text
core_dataset_version
core_dataset_schema_version
```

Бұл bundled version; ол ағымдағы дерекқорға міндетті түрде орнатылған дегенді білдірмейді. Нақты DB күйі `/api/v1/core-dataset/status` арқылы тексеріледі.

## Болашақ жаңарту ережелері

Келесі snapshots:

- жаңа `dataset_version` алуы;
- бір объект үшін stable `external_id` сақтауы;
- геологиялық фактілерге дәлелді source/provenance беруі;
- checksum және reference validation өтуі;
- external немесе AI-derived data-ны автоматты verified master етпеуі;
- schema үйлесімді болса, `.exe`/app version-нан тәуелсіз жаңартылуы тиіс.

Bundle signature, download/update channel және алдыңғы installed version-ға rollback — келесі кезеңдер. Schema v1 dataset lifecycle-ды Alembic lifecycle-дан қазірдің өзінде бөледі.
