# GeoKZ v0.2-dev

GeoKZ — доказательная геологическая информационная система Казахстана для хранения, структурирования, поиска, пространственного анализа и экспертной проверки геологических знаний с обязательной прослеживаемостью данных до первичных и внешних источников.

## Ключевые принципы

- **Три языка:** русский (`ru`), казахский (`kk`) и английский (`en`).
- **Evidence-first:** факт хранится отдельно от подтверждений и источников.
- **Human-in-the-loop:** ИИ и внешние API не публикуют проверенные факты автоматически.
- **Offline-capable core:** базовая информация GeoKZ доступна без обязательного интернета.
- **Обновляемые данные:** внешний контент и GeoKZ Core Dataset обновляются независимо от версии приложения.
- **Data provenance:** сохраняются источник, исходная запись, версия набора, дата получения, checksum и история синхронизаций.
- **GIS-first storage:** PostgreSQL/PostGIS, EPSG:4326, GeoJSON; далее GeoPackage, OGC API Features и QGIS-интеграция.

## Текущий стек

- FastAPI;
- PostgreSQL 17 + PostGIS 3.5;
- асинхронный SQLAlchemy 2;
- Alembic;
- Pydantic;
- Docker Compose;
- GitHub Actions CI;
- PySide6 запланирован для Windows-клиента.

## Что уже реализовано

- источники, документы и страницы;
- геологические объекты и мультиязычные названия;
- факты и доказательства;
- скважины и интервалы;
- конфликты;
- базовые CRUD API;
- пилотные данные по Прикаспийской впадине и Даулеталы;
- PostGIS, `pg_trgm`, `unaccent`;
- health checks;
- CI;
- API «О программе» на `ru/kk/en`;
- первый слой внешних интеграций: источники, RAW-записи, sync runs и связи с объектами GeoKZ;
- общий контракт `ExternalDataConnector`;
- SHA-256 checksum для выявления изменений внешних записей.

## Архитектурное правило

Рабочая база не зависит от нейросети и внешнего API. Система должна оставаться полезной без интернета.

```text
PySide6 / Web / QGIS
        │
        ▼
    FastAPI /api/v1
        │
        ▼
 Application Layer
        │
        ▼
 PostgreSQL/PostGIS
```

Внешние данные проходят отдельный pipeline:

```text
External API
    ↓
Connector
    ↓
RAW / staging
    ↓
checksum + diff
    ↓
normalization
    ↓
entity matching
    ↓
review
    ↓
verified GeoKZ data
```

Внешняя синхронизация не должна напрямую переписывать проверенные `facts` и `geological_entities`.

## Трёхъязычность

GeoKZ поддерживает:

- русский;
- қазақ тілі;
- English.

Локализуются UI, предметные названия, справочники, пользовательская документация и display-поля API. Исходные цитаты, OCR/raw text и RAW payload внешнего источника сохраняются без перевода.

Подробнее: [`docs/I18N.md`](docs/I18N.md).

## Внешние открытые источники

Планируемый приоритет:

1. Kazakhstan Open Data (`data.egov.kz`);
2. USGS;
3. Macrostrat;
4. OneGeology / OGC services;
5. Copernicus — на более позднем этапе.

Каждый источник подключается отдельным адаптером и обязан сохранять лицензию/условия использования, RAW payload и историю обновлений.

Подробнее: [`docs/PROJECT_PLAN_V0_2.md`](docs/PROJECT_PLAN_V0_2.md).

## Быстрый запуск в Windows через Docker Desktop

Требования:

- Git;
- Docker Desktop с `docker compose`.

```powershell
Copy-Item .env.example .env
./scripts/dev.ps1
```

Либо:

```powershell
docker compose up --build
```

После запуска:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- live check: `http://localhost:8000/health/live`
- readiness/PostGIS: `http://localhost:8000/health/ready`
- о программе: `http://localhost:8000/api/v1/about?lang=ru`
- внешние источники: `http://localhost:8000/api/v1/integrations/sources`

## Миграции и тесты

```powershell
docker compose exec api alembic upgrade head
docker compose exec api pytest
docker compose exec api ruff check .
```

## Пилотные данные

```powershell
docker compose exec api python -m scripts.seed_pilot
```

Пилот включает:

- том XXI «Геология СССР. Западный Казахстан», книги 1 и 2;
- документ 2017 года по Даулеталы;
- Прикаспийскую впадину;
- Южно-Эмбинское поднятие;
- месторождение Даулеталы.

## Структура

```text
app/
├── api/                  HTTP API
├── core/                 конфигурация и метаданные проекта
├── integrations/         контракты внешних источников
├── models/               SQLAlchemy-модели
└── schemas/              Pydantic-схемы
migrations/               Alembic
scripts/                  seed/служебные сценарии
tests/                    автоматические проверки
docs/                     архитектура и план развития
packaging/windows/        заготовка Windows installer
```

## Документация

- [`docs/PROJECT_PLAN_V0_2.md`](docs/PROJECT_PLAN_V0_2.md) — основной roadmap;
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — архитектурные принципы;
- [`docs/I18N.md`](docs/I18N.md) — RU/KK/EN;
- [`docs/WINDOWS_DESKTOP_PLAN.md`](docs/WINDOWS_DESKTOP_PLAN.md) — Windows-клиент;
- [`docs/ABOUT.md`](docs/ABOUT.md) — описание проекта и автор.

## Автор

**Sarmuldin Rinat**  
Email: **ura07srr@gmail.com**

Repository: `07Rinat07/GeoKZ`
