# GeoKZ — привязка controlled vocabularies к subsurface-моделям (RU)

Статус: `v0.3`, 2026-09-05.

## Назначение

После появления persistent controlled vocabulary registry GeoKZ добавляет отдельные canonical-code поля к рабочим моделям скважин, керна, ГИС и испытаний. Это не миграция исходного текста в новый формат: существующие RAW/source поля сохраняются без изменения, а canonical code записывается рядом как результат безопасной нормализации.

## Новые поля

- `WellInterval.lithologies` остаётся исходным списком; `WellInterval.lithology_codes` хранит canonical `lithology` codes.
- `WellInterval.flow_rate_unit` остаётся исходной строкой; `flow_rate_unit_code` хранит canonical `unit` code.
- `CoreSample.lithologies` сохраняется; `CoreSample.lithology_codes` добавляет canonical codes.
- `WellMarker.marker_type` сохраняется; `marker_type_code` связывает значение с vocabulary `marker_type`.
- `WellLogCurve.property_kind` сохраняется; `property_kind_code` использует vocabulary `property_kind`.
- `WellLogCurve.unit_original` и существующий `canonical_unit` не удаляются; `unit_code` хранит стабильный controlled code.
- `WellTest.oil_rate_unit`, `gas_rate_unit`, `water_rate_unit` сохраняются; рядом добавлены `oil_rate_unit_code`, `gas_rate_unit_code`, `water_rate_unit_code`.

Alembic revision: `20260905_0007`. Новые scalar code columns nullable, поэтому миграция обратно совместима с существующими данными. Новые списки `lithology_codes` создаются как пустые JSONB-массивы и не пытаются автоматически переписать исторические записи при upgrade.

## DomainVocabularyNormalizer

`app.application.domain_vocabulary.DomainVocabularyNormalizer` выполняет только deterministic exact resolution через существующий controlled vocabulary service. Он не делает fuzzy/semantic auto-match и не выполняет commit: транзакцией владеет вызывающий application/import/review workflow.

Поддерживаются отдельные операции:

```text
normalize_well_interval
normalize_core_sample
normalize_well_marker
normalize_well_log_curve
normalize_well_test
```

Scalar field обновляется только когда resolver вернул `RESOLVED`. Для `UNRESOLVED` или `AMBIGUOUS` существующий canonical code остаётся неизменным и в report добавляется issue.

Для list-полей действует более строгая атомарная политика: если хотя бы одна исходная литология не разрешена однозначно, `lithology_codes` целиком не меняется. Это не позволяет частично нормализованному списку выглядеть полным и не уничтожает ранее экспертно подтверждённое значение.

## Пример

Исходная запись:

```text
lithologies = ["Песчаник", "неразобранная порода"]
lithology_codes = ["reviewed-existing-code"]
```

Если `Песчаник` разрешается, а второе значение получает `UNRESOLVED`, normalizer возвращает issue и оставляет `lithology_codes` прежним. Исходный список также не меняется.

Для well-log curve:

```text
mnemonic_original = GR
property_kind = GR
property_kind_code = gamma_ray
unit_original = API
unit_code = api_deg
```

`mnemonic_original`, `property_kind` и `unit_original` остаются частью provenance; canonical codes используются для поиска, фильтрации, сопоставления и будущего UI.

## Правила безопасности

1. RAW/source value никогда не удаляется из-за успешного resolve.
2. Только active controlled terms участвуют в normalization.
3. `UNRESOLVED` и `AMBIGUOUS` не очищают существующий canonical assignment.
4. List normalization атомарна: partial success не публикуется как полный canonical список.
5. Normalizer не делает `commit()` и не скрывает review boundary.
6. Bulk backfill всех исторических записей автоматически не запускается. Он должен быть отдельным reviewable workflow с отчётом unresolved/ambiguous значений.
7. Controlled code пока не является заменой evidence/source provenance и не повышает `VerificationStatus` геологического объекта.

## Следующий этап

После завершения controlled-vocabulary P0 следующий roadmap-пункт — normalizer/review для реестра лицензий на геологическое изучение недр после повторной проверки официального mapping, license/terms и качества данных. До этого можно отдельно добавить UI helpers, отображающие raw value и canonical code рядом, но UI не должен сам реализовывать matching rules.
