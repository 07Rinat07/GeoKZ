# GeoKZ — бақыланатын геологиялық сөздіктер (KK)

Күйі: foundation `v0.3`, 2026-09-05.

## Мақсаты

GeoKZ төрт санат үшін persistent бақыланатын терминдер реестрін енгізеді: `lithology`, `marker_type`, `property_kind` және `unit`. Мақсат — API, importer, болашақ PySide6 client және external connector үшін тұрақты canonical code беру, бірақ бастапқы дереккөз мәтінін үнсіз өзгертпеу.

Негізгі қағида: **RAW/source wording жеке сақталады және сөздік оны қайта жазбайды**. Мысалы, LAS mnemonic, автор берген литология сипаттамасы немесе бастапқы өлшем бірлігі бастапқы өрісте/RAW payload ішінде қалады. Controlled vocabulary тек бөлек normalization қабатында canonical code ұсынады.

## Деректер моделі

`controlled_vocabulary_terms` кестесі мыналарды сақтайды:

- `vocabulary` — төрт тұрақты санаттың бірі;
- `code` — сол санаттағы canonical GeoKZ code;
- `name_ru`, `name_kk`, `name_en` — міндетті display names;
- `aliases` — қауіпсіз exact matching үшін рұқсат етілген атау нұсқалары;
- `description` — міндетті емес түсіндірме;
- `source_reference` — терминнің provenance/негізі;
- `metadata` — кеңейтілетін техникалық атрибуттар, мысалы `symbol`, `quantity_kind`, typical mnemonics;
- `is_active` — термин жаңа normalization кезінде қолданылатынын көрсетеді.

Бірегейлік `(vocabulary, code)` жұбымен қамтамасыз етіледі. Геологиялық терминдер бір үлкен Python Enum түрінде қатырылмайды: реестр пәндік сөздікті application code өзгерісінсіз кеңейтуге мүмкіндік береді.

## API

Санаттар каталогы:

```text
GET /api/v1/vocabularies?lang=kk
```

Бір санаттың терминдері:

```text
GET /api/v1/vocabularies/lithology/terms?lang=kk
GET /api/v1/vocabularies/unit/terms?lang=kk&include_inactive=false
```

Бастапқы мәндерді пакетпен қауіпсіз resolve ету:

```text
POST /api/v1/vocabularies/property_kind/resolve?lang=kk
```

Сұрау мысалы:

```json
{
  "values": ["GR", "Gamma ray", "белгісіз параметр"]
}
```

Әр мән үшін жауап `RESOLVED`, `UNRESOLVED` немесе `AMBIGUOUS` болады. Бұл кезеңде fuzzy matching жоқ. GeoKZ бос орындарды қалыпқа келтіріп, регистрге тәуелсіз түрде `code`, үш тілдегі атаулар және aliases бойынша exact matching жасайды. Егер бір alias бірнеше терминге сәйкес келсе, жүйе біреуін кездейсоқ таңдамайды — `AMBIGUOUS` қайтарады.

## Bootstrap

Бастапқы сөздік:

```text
data/bootstrap/controlled_vocabularies.json
```

Бұл Қазақстан геологиясының толық ресми классификациясы емес, **initial internal dictionary**. Ол lithology, marker types, well-log/property kinds және units үшін минималды бастапқы жиын береді. Production кеңейтуі subject-matter review және міндетті `source_reference` талап етеді.

Идемпотентті жүктеу:

```text
python -m scripts.seed_controlled_vocabularies
```

Script `(vocabulary, code)` бойынша upsert орындайды. Schema migration және dataset seeding әдейі бөлінген: Alembic кесте құрылымын жасайды, bootstrap деректерді бөлек жүктейді.

## Қауіпсіздік және provenance ережелері

1. Controlled term құжаттағы, LAS/DLIS/WITSML ішіндегі, external API-дегі немесе expert input-тағы бастапқы мәнді жоймайды.
2. Bootstrap терминдерінің өзінде де `source_reference` міндетті.
3. `is_active=false` термин default resolve процесіне қатыспайды.
4. Болашақ fuzzy/semantic matching тек review candidate жасай алады; canonical code автоматты түрде ауыстырылмайды.
5. Public write/edit API әзірге әдейі жоқ. Admin write workflow Authentication + AuditLog/revisions енгізілгеннен кейін ғана қосылады, сонда терминология өзгерісінің авторы мен тарихы сақталады.
6. Units canonical code және `symbol`/`quantity_kind` metadata-мен беріледі; ұқсас unit string негізінде numeric conversion автоматты түрде орындалмайды.

## Келесі қадам

Foundation-нан кейін canonical codes domain model-дерге **raw fields сақтала отырып** қосылады: lithology үшін `WellInterval/CoreSample`, marker type үшін `WellMarker`, property kind/unit үшін `WellLogCurve`, сондай-ақ test/interval rate units. Migration backward-compatible болуы тиіс, ал normalization raw value, resolved canonical code және unresolved/review-required күйін анық ажыратуы керек.
