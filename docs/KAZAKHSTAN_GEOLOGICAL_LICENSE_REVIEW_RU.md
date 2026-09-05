# GeoKZ — обработка и проверка лицензий на геологическое изучение недр (RU)

Статус: `v0.3`, 2026-09-05.

## Источник

GeoKZ использует официальный ресурс Kazakhstan Open Data:

- GeoKZ code: `kz-egov-geological-study-licenses`;
- официальный `apiUri`: `zher_koinauyn_geologiyalyk_zer2`;
- версия: `v6`;
- `record_type`: `geological_study_license`;
- владелец набора на портале: Комитет геологии Министерства промышленности и строительства Республики Казахстан;
- на карточке набора на момент проверки 2026-09-05 указан статус актуального опубликованного набора, 476 записей и обновление 2026-05-20.

Перед production-sync необходимо проверять текущие metadata и mapping самого портала через:

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/schema
```

GeoKZ не считает названия технических полей вечными. Официальный `apiUri` и `version` хранятся отдельно, а RAW payload сохраняется без переименования полей.

## Подтверждённые пользовательские поля карточки v6

Карточка официального набора показывает административные сведения:

1. вид лицензии на недропользование;
2. номер и дата лицензии;
3. срок лицензии;
4. основание выдачи;
5. государственный орган, выдавший лицензию;
6. сведения о лице, которому выдана лицензия.

Normalizer извлекает только то, что можно получить из этих административных полей: `license_number`, `issue_date`, `license_type_raw`, `study_scope_code`, `term_raw`, `basis_raw`, `issuing_authority_raw`, `holder_raw`, `holder_bin` и `source_fields`. Исходные строки остаются в `raw_payload`.

## Почему нет автоматической связи с месторождением

Проверенная карточка `v6` не предоставляет стабильный идентификатор геологического объекта/месторождения и его геометрию, достаточные для детерминированного entity matching. Поэтому GeoKZ **не создаёт `ExternalEntityLink` и не создаёт `GeologicalEntity` из этой записи автоматически**.

Лицензия — административная запись. Её наличие само по себе не подтверждает координаты месторождения, литологию, запасы, нефтегазоносность, интервалы скважин или другую геологическую интерпретацию.

## Pipeline

```text
schema → sync → RAW → process → REVIEW_REQUIRED → accept / reject
```

Синхронизация:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/sync
```

Нормализация:

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/process
```

После успешной нормализации запись получает `normalization_status=NORMALIZED`, `review.status=PENDING`, `review.entity_matching=NOT_APPLICABLE` и `ExternalRecord.status=REVIEW_REQUIRED`.

Если mapping изменился и номер/дату нельзя определить однозначно, normalizer не угадывает значение: запись остаётся `REVIEW_REQUIRED` с `normalization_status=ERROR`. Такую запись нельзя принять до исправления mapping/normalizer.

## Очередь review

```text
GET /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records
```

Ответ сохраняет рядом:

- `raw_payload` — исходную запись портала;
- `normalized_payload` — отдельное представление GeoKZ;
- `status`;
- `reviewed_by`;
- `reviewed_at`;
- `review_comment`.

### Принять административную запись

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/accept
```

Принятие означает только: эксперт проверил корректность нормализованного административного представления относительно доступного upstream payload. `ExternalRecord` становится `ACCEPTED`. Это **не** означает `GeologicalEntity=VERIFIED` и не публикует геологический факт.

### Отклонить запись

```text
POST /api/v1/integrations/kazakhstan/kz-egov-geological-study-licenses/review/records/{record_id}/reject
```

Для reject обязателен комментарий. Причиной может быть повреждённая запись, неверное извлечение, неоднозначный mapping или другой дефект, требующий ручной проверки.

## Изменения upstream

Если уже обработанная запись приходит с новым checksum, sync переводит её в `CHANGED`. Следующий `process` очищает прежнее record-level решение (`reviewed_by`, `reviewed_at`, `review_comment`) и возвращает запись в `REVIEW_REQUIRED`. Старое человеческое решение не переносится автоматически на изменившийся upstream payload.

Исчезновение upstream не должно превращаться в hard delete проверенных данных GeoKZ: используется отдельная семантика `is_deleted_upstream`/tombstone.

## API key

Для фактической загрузки API v4 требуется ключ портала. Он хранится только локально:

```env
GEOKZ_EGOV_API_KEY=ВАШ_РЕАЛЬНЫЙ_КЛЮЧ
```

Ключ запрещено коммитить в Git, документацию, issue, PR или скриншоты. Получение и настройка описаны в `docs/EXTERNAL_API_KEYS_RU.md`.

## Правила provenance и безопасности

- RAW не переписывается normalizer-ом.
- Символы исходной записи, включая `№` в номере лицензии, не должны изменяться из-за технической Unicode-нормализации.
- Контентный fallback используется только как совместимость при изменении технических имён полей; официальный mapping всё равно проверяется через `/schema`.
- Не выполняется fuzzy/semantic matching лицензии с месторождениями.
- ACCEPTED административная запись не повышает `VerificationStatus` геологических объектов.
- Все будущие связи лицензии с территорией/лицензионным блоком должны появляться только после появления в источнике проверяемого идентификатора или геометрии и отдельного review workflow.

## Definition of Done

Изменение этого workflow считается завершённым только после unit tests, PostgreSQL/PostGIS integration tests, миграции до Alembic `20260905_0008`, синхронизации документации RU/KK/EN и зелёного exact-head CI/PR-CI.
