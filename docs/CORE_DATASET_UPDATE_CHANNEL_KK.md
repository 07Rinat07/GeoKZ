# GeoKZ — Core Dataset жаңарту арнасы (KK)

Контракт нұсқасы: `v0.3`.

## Мақсаты

GeoKZ Core Dataset қолданба нұсқасы мен дерекқор схемасынан тәуелсіз жаңартылады. Онлайн арна тек сенімді, қолтаңбаланған GeoKZ snapshot пакеттеріне арналған және жұмыс станциясындағы еркін файлдарды импорттау механизмі емес. Update server қолжетімсіз болса да, GeoKZ жергілікті режимде жұмысын жалғастырады: bundled Core Dataset және PostgreSQL/PostGIS деректері сақталады.

Admin endpoints:

```text
GET  /api/v1/core-dataset/update/status
POST /api/v1/core-dataset/update/apply?dry_run=true&lang=kk
POST /api/v1/core-dataset/update/apply?lang=kk
POST /api/v1/core-dataset/update/rollback?lang=kk
```

Update және rollback операциялары `admin` рөлін талап етеді. Bundled dataset күйі бұрынғыдай `/api/v1/core-dataset/status` арқылы бөлек оқылады.

## Сенім моделі

Update descriptor — `channel_schema_version=1` схемасындағы JSON. Онда `dataset_code`, `dataset_version`, `core_dataset_schema_version`, manifest SHA-256, ZIP үшін HTTPS URL, bundle SHA-256, жариялау уақыты, compatibility талаптары, `key_id` және `signature` бар.

Қолтаңба Ed25519 арқылы тексеріледі. GeoKZ runtime тек сенімді **public key** сақтайды. Private signing key `.env`, Git repository, desktop client немесе application database ішінде болмауы тиіс.

Конфигурация:

```env
GEOKZ_CORE_DATASET_UPDATE_MANIFEST_URL=https://updates.example/geokz/core/channel.json
GEOKZ_CORE_DATASET_UPDATE_TRUSTED_PUBLIC_KEYS={"prod-2026":"<base64-raw-ed25519-public-key>"}
GEOKZ_CORE_DATASET_UPDATE_CACHE_DIR=data/runtime/core_dataset_updates
GEOKZ_CORE_DATASET_UPDATE_MAX_BYTES=134217728
```

URL немесе trusted-key map бос болса, арна `DISABLED`. Descriptor URL және `bundle_url` тек HTTPS болуы керек. Redirect автоматты түрде орындалмайды, сондықтан update origin үнсіз ауыстырылмайды.

## Орнатуға дейінгі тексеру

GeoKZ fail-closed ретімен жұмыс істейді:

1. descriptor алу;
2. `key_id` trust store ішінде бар екенін және Ed25519 signature canonical JSON үшін жарамды екенін тексеру;
3. compatibility gate орындау;
4. ZIP-ті size limit арқылы жүктеу;
5. ZIP SHA-256 мәнін қолтаңбаланған descriptor-пен салыстыру;
6. staging/cache ішіне path traversal, absolute path және symlink қорғанысымен шығару;
7. `manifest.json` файлын қолданыстағы Core Dataset validator арқылы тексеру;
8. manifest SHA-256, `dataset_code`, `dataset_version`, `schema_version` мәндерін descriptor-пен салыстыру;
9. тек содан кейін transactional activation бастау.

Signature, checksum, manifest немесе compatibility қатесі болса, master data өзгермейді.

## Compatibility gate

Үш тәуелсіз compatibility өлшемі тексеріледі:

- application: `minimum_app_version` ағымдағы `PROJECT_VERSION` мәнімен салыстырылады;
- database: `required_database_revision` ағымдағы `alembic_version` мәніне дәл сәйкес болуы тиіс;
- Core Dataset format: `core_dataset_schema_version` ағымдағы `CORE_DATASET_SCHEMA_VERSION` мәніне сәйкес болуы керек.

Update state үшін ағымдағы migration — `20260905_0011`. Онлайн жаңарту алдында bundled `geokz-core` baseline орнатылған болуы міндетті; network bootstrap-ты алмастырмайды.

`/api/v1/core-dataset/update/status` келесі state мәндерінің бірін қайтарады:

- `DISABLED` — арна конфигурацияланбаған;
- `FAILED` — descriptor қауіпсіз алынбады немесе тексерілмеді;
- `CURRENT` — орнатылған manifest signed release-пен бірдей;
- `AVAILABLE` — жаңа compatible release бар;
- `INCOMPATIBLE` — signature дұрыс, бірақ application/database/Core Dataset schema талаптары сәйкес емес.

Response ішінде `signature_verified`, `compatible`, `compatibility_issues`, installed/available version және rollback availability бөлек беріледі.

## Transactional activation

Admin алдымен `dry_run=true` орындай алады. Бұл signature, checksum, ZIP, manifest және Core Dataset validation толық орындайды, бірақ DB activation жасамайды.

Нақты apply кезінде пакет алдымен network/staging деңгейінде дайындалып тексеріледі. Содан кейін PostgreSQL advisory transaction lock және `CoreDatasetState` row lock алынады. Lock алынған соң state қайта оқылады. Егер update дайындалып жатқан уақытта басқа процесс installed manifest-ті өзгертсе, операция conflict арқылы тоқтайды және қайта іске қосылуы керек. Network I/O row lock астында орындалмайды.

Activation алдында previous snapshot metadata сақталады: version, schema, manifest SHA-256, source path, file checksums және item counts. Existing Core Dataset importer upsert-ті және `CoreDatasetState` жаңартуын бір transaction ішінде аяқтайды.

AuditLog authenticated admin-ды, `signed_online_update` reason, from/to versions, manifest SHA-256, bundle SHA-256, `key_id` және descriptor URL сақтайды. Client reviewer/admin identity-ді request body арқылы алмастыра алмайды.

## Rollback

GeoKZ бір previous snapshot үшін қауіпсіз rollback қолдайды:

```text
POST /api/v1/core-dataset/update/rollback?lang=kk
```

Rollback жаңа версияда пайда болған барлық жолдарды blind hard-delete жасамайды. Core Dataset importer архитектурасы upsert-only, себебі кейін user/expert толықтырған master data-ны жоюға болмайды.

Сондықтан rollback current және previous bundle ішіндегі `external_id` жиындары sources, regions, entities және facts үшін бөлек бірдей болғанда ғана рұқсат етіледі. Identity set өзгерсе, rollback блокталады. Бұл жаңа master data-ны үнсіз жоюдан қорғайды.

Rollback алдында екі local manifest, previous manifest SHA-256 және identity sets тексеріледі. Одан кейін advisory/row lock алынып, state concurrent process арқылы өзгермегені қайта тексеріледі. Сәтті rollback AuditLog ішінде `safe_rollback` reason арқылы жазылады.

Previous cache manifest жоқ болса немесе checksum сәйкес болмаса, rollback unverifiable ретінде қабылданбайды.

## Desktop және пайдалану

PySide6 desktop PostgreSQL-ға тікелей қосылмайды. Ол тек GeoKZ HTTP API арқылы update status/apply/rollback сұрауларын орындайды. UI `CURRENT`, `AVAILABLE`, `INCOMPATIBLE`, `FAILED`, signing `key_id`, compatibility issues және rollback availability көрсетуі тиіс.

`AVAILABLE` release автоматты түрде орнатылмауы керек; admin explicit action орындайды. Online update қатесі бұрын орнатылған геологиялық деректерді қарауды блоктамауы тиіс.

## Деректер инварианттары

Core Dataset update GeoKZ-дың негізгі ережелерін өзгертпейді:

- verified external link `GeologicalEntity=VERIFIED` мәртебесін автоматты түрде бермейді;
- update master data-ны үнсіз жоймайды;
- provenance және evidence сақталады;
- external network optional enrichment/update layer болып қалады;
- PostgreSQL/PostGIS local current state көзі болып қалады;
- install/update/rollback тарихы authenticated admin арқылы AuditLog ішінде көрінуі тиіс.
