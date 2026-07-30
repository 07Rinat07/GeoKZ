# Проверка каркаса v0.1

При сборке артефакта выполнены:

- компиляция всех Python-файлов через `compileall`;
- загрузка `pyproject.toml` стандартным `tomllib`;
- регистрация всех SQLAlchemy-моделей и `configure_mappers()`;
- тесты `tests/test_config.py` и `tests/test_health.py`;
- генерация offline SQL для `alembic upgrade head --sql`.

Результат: проверки прошли успешно.

Полный запуск `docker compose up --build` в среде генерации не выполнялся,
поскольку Docker Engine в ней отсутствует. Поэтому первый запуск на Windows
следует считать интеграционной проверкой реальных образов и сетевого окружения.
