# GeoKZ — controlled vocabularies және subsurface model bindings (KK)

Күйі: `v0.3`, 2026-09-05.

## Мақсаты

Persistent controlled vocabulary registry енгізілгеннен кейін GeoKZ well, core, well logs және tests модельдеріне бөлек canonical-code өрістерін қосады. Бұл бастапқы мәтінді жаңа форматқа ауыстыру емес: RAW/source fields өзгеріссіз сақталады, ал canonical code қауіпсіз normalization нәтижесі ретінде жеке жазылады.

## Жаңа өрістер

- `WellInterval.lithologies` бастапқы тізім болып қалады; `WellInterval.lithology_codes` canonical `lithology` codes сақтайды.
- `WellInterval.flow_rate_unit` бастапқы unit string болып қалады; `flow_rate_unit_code` canonical `unit` code сақтайды.
- `CoreSample.lithologies` сақталады; `CoreSample.lithology_codes` canonical codes қосады.
- `WellMarker.marker_type` сақталады; `marker_type_code` `marker_type` vocabulary term-ін көрсетеді.
- `WellLogCurve.property_kind` сақталады; `property_kind_code` `property_kind` vocabulary code қолданады.
- `WellLogCurve.unit_original` және бұрынғы `canonical_unit` жойылмайды; `unit_code` тұрақты controlled code сақтайды.
- `WellTest.oil_rate_unit`, `gas_rate_unit`, `water_rate_unit` сақталады; қосымша `oil_rate_unit_code`, `gas_rate_unit_code`, `water_rate_unit_code` бар.

Alembic revision: `20260905_0007`. Scalar code columns nullable, сондықтан migration бұрынғы деректермен backward-compatible. `lithology_codes` JSONB тізімдері бос массивпен қосылады және schema upgrade кезінде historical records автоматты түрде қайта түсіндірілмейді.

## DomainVocabularyNormalizer

`app.application.domain_vocabulary.DomainVocabularyNormalizer` existing controlled vocabulary service арқылы deterministic exact resolution ғана орындайды. Fuzzy/semantic auto-match жоқ және normalizer өзі `commit()` жасамайды: transaction ownership importer/application/review workflow жағында қалады.

Қолдау көрсетілетін операциялар:

```text
normalize_well_interval
normalize_core_sample
normalize_well_marker
normalize_well_log_curve
normalize_well_test
```

Scalar field resolver `RESOLVED` қайтарған кезде ғана жаңартылады. `UNRESOLVED` немесе `AMBIGUOUS` болса existing canonical code өшірілмейді; report ішінде issue беріледі.

List fields үшін қатаң atomic policy қолданылады: бастапқы lithology мәндерінің кемінде біреуі бірмәнді resolve болмаса, `lithology_codes` толық өзгеріссіз қалады. Бұл partial normalization нәтижесінің complete canonical list болып көрінуіне жол бермейді және бұрынғы reviewed assignment-ты сақтайды.

## Мысал

Бастапқы record:

```text
lithologies = ["Құмтас", "анықталмаған жыныс"]
lithology_codes = ["reviewed-existing-code"]
```

Егер `Құмтас` resolve болып, екінші мән `UNRESOLVED` болса, normalizer issue қайтарады және `lithology_codes` бұрынғы қалпында қалады. Raw list те өзгермейді.

Well-log curve мысалы:

```text
mnemonic_original = GR
property_kind = GR
property_kind_code = gamma_ray
unit_original = API
unit_code = api_deg
```

`mnemonic_original`, `property_kind`, `unit_original` provenance бөлігі болып қала береді. Canonical codes search, filtering, correlation және future UI үшін қолданылады.

## Қауіпсіздік ережелері

1. Successful resolve RAW/source value-ді ешқашан жоймайды.
2. Normalization тек active controlled terms қолданады.
3. `UNRESOLVED` және `AMBIGUOUS` existing canonical assignment-ты тазаламайды.
4. List normalization atomic: partial success complete canonical list ретінде жарияланбайды.
5. Normalizer `commit()` жасамайды және review boundary-ді жасырмайды.
6. Historical records үшін automatic bulk backfill жоқ. Ол unresolved/ambiguous report бар жеке reviewable workflow болуы тиіс.
7. Controlled code evidence/source provenance-тің орнына жүрмейді және geological object `VerificationStatus` мәнін автоматты көтермейді.

## Келесі кезең

Controlled-vocabulary P0 аяқталғаннан кейін roadmap бойынша келесі пункт — geological study licenses registry үшін normalizer/review. Оған дейін official mapping, license/terms және data quality қайта тексерілуі тиіс. UI raw value мен canonical code-ты қатар көрсете алады, бірақ matching business rules клиентте қайталанбауы керек.
