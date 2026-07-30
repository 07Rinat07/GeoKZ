# GeoKZ Backend v0.1

Запускаемый каркас доказательного геологического справочника Казахстана.

## Что входит

- FastAPI API;
- PostgreSQL 17 + PostGIS 3.5;
- асинхронный SQLAlchemy 2;
- Alembic и начальная миграция;
- расширения `postgis`, `pg_trgm`, `unaccent`;
- модели источников, документов, страниц, геологических объектов, фактов,
  доказательств, скважин, интервалов и конфликтов;
- базовые CRUD-маршруты;
- пилотное заполнение для Прикаспийской впадины и Даулеталы;
- подготовленная граница между backend и будущим Windows-клиентом.

## Архитектурное правило

Рабочая база не зависит от нейросети. ИИ может готовить черновые JSON/CSV/JSONL,
но публикация фактов выполняется только после проверки человеком.

```text
Windows-клиент / Web-клиент
            │
            ▼
         FastAPI
            │
            ▼
SQLAlchemy + PostgreSQL/PostGIS
```

## Быстрый запуск в Windows через Docker Desktop

Требования для разработки:

- Git;
- Docker Desktop с командой `docker compose`.

В PowerShell:

```powershell
Copy-Item .env.example .env
./scripts/dev.ps1
```

Либо вручную:

```powershell
docker compose up --build
```

После запуска:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- проверка процесса: `http://localhost:8000/health/live`
- проверка БД и PostGIS: `http://localhost:8000/health/ready`

## Пилотные данные

```powershell
docker compose exec api python -m scripts.seed_pilot
```

Скрипт добавляет:

- том XXI «Геология СССР. Западный Казахстан», книги 1 и 2;
- документ 2017 года по Даулеталы;
- Прикаспийскую впадину;
- Южно-Эмбинское поднятие;
- месторождение Даулеталы.

Скрипт идемпотентный: повторный запуск не создаёт дубликаты.

## Основные команды

```powershell
# Запуск
docker compose up --build

# Остановка
docker compose down

# Остановка с удалением тестовой базы
docker compose down -v

# Применение миграций
docker compose exec api alembic upgrade head

# Текущая миграция
docker compose exec api alembic current

# Новая миграция после изменения моделей
docker compose exec api alembic revision --autogenerate -m "описание"

# Тесты
docker compose exec api pytest

# Линтер
docker compose exec api ruff check .
```

## Локальный запуск Python без контейнера API

Базу можно оставить в Docker, а API запустить из виртуального окружения:

```powershell
Copy-Item .env.example .env
# В .env оставить host=localhost в GEOKZ_DATABASE_URL.

docker compose up -d db
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Структура

```text
app/
├── api/                 HTTP-маршруты
├── core/                конфигурация и подключение к БД
├── models/              SQLAlchemy-модели
└── schemas/             Pydantic-схемы
migrations/              Alembic
scripts/                 служебные и seed-скрипты
docs/                    архитектура и Windows-план
packaging/windows/       заготовка установщика
```

## Будущее Windows-приложение

Docker используется только разработчиками. План конечной поставки:

1. интерфейс на PySide6;
2. клиент общается с тем же FastAPI-контрактом;
3. сборка `GeoKZ.exe` через `pyside6-deploy` или PyInstaller;
4. установщик через Inno Setup либо MSIX;
5. два режима работы:
   - локальная база PostgreSQL/PostGIS на одном компьютере;
   - подключение к центральному серверу организации.

Подробности: [`docs/WINDOWS_DESKTOP_PLAN.md`](docs/WINDOWS_DESKTOP_PLAN.md).

## Важное ограничение версии 0.1

Это backend-каркас, а не готовый пользовательский справочник. В нём ещё нет:

- полноценного интерфейса;
- импорта PDF/DOCX;
- редакторской панели проверки;
- геологической карты;
- авторизации и ролей;
- хранения файлов в объектном хранилище.

Эти модули можно добавлять независимо, не меняя базовый контракт данных.
