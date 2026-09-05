# GeoKZ — аутентификация, рөлдер, аудит және ревизия тарихы

Контракт нұсқасы: `v0.3`.

## Мақсаты

GeoKZ геологиялық ақпаратты оқуды scientific master data өзгерту және сараптамалық шешім қабылдау операцияларынан бөледі. Аутентификацияның негізгі мақсаты — әрбір өзгерістің нақты авторы, рөлі, себебі және өзгермейтін тарихы болуы.

## Рөлдер

- `editor` — `Source`, `GeologicalEntity`, `Fact` жасайды және өңдейді, бірақ `verification_status` мәнін `DRAFT` деңгейінен жоғары көтере алмайды.
- `expert` — ғылыми review орындайды, master data-ны `REVIEWED`/`VERIFIED` күйіне ауыстыра алады және сыртқы review queue бойынша шешім қабылдайды.
- `admin` — expert/editor құқықтарына қоса local user accounts басқарады, bundled Core Dataset орнатады және толық audit log оқиды.

Рөл тек backend ішінде тексеріледі. UI қауіпсіздік шекарасы болып саналмайды.

## Бірінші administrator

Алғашқы local account GeoKZ серверінде/жұмыс станциясында CLI арқылы жасалады. Password command-line argument ретінде берілмейді, сондықтан shell history ішінде қалмайды:

```text
python -m scripts.auth create-user --username admin --display-name "GeoKZ Administrator" --role admin
```

Команда password мәнін екі рет интерактивті сұрайды. Минималды ұзындығы — 12 символ. Кейінгі accounts-ты admin API арқылы жасайды.

## Login және session

```text
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

Login сәтті болса backend opaque bearer token қайтарады. Token-ның өзі PostgreSQL-да сақталмайды; тек SHA-256 hash сақталады. Password salted `scrypt-v1` hash ретінде сақталады. Session мерзімі:

```env
GEOKZ_AUTH_SESSION_HOURS=12
```

Protected request үшін `Authorization: Bearer <token>` қолданылады. Logout session-ға `revoked_at` қояды, сондықтан бұрынғы token HTTP `401` алады.

## User management

Тек `admin`:

```text
POST /api/v1/auth/users
GET  /api/v1/auth/users
```

API `password_hash` немесе bearer token hash мәндерін қайтармайды.

## Scientific master-data writes

Source, geological entity және fact жасау/өзгерту authenticated session талап етеді:

```text
POST  /api/v1/sources
PATCH /api/v1/sources/{source_id}
POST  /api/v1/entities
PATCH /api/v1/entities/{entity_id}
POST  /api/v1/facts
PATCH /api/v1/facts/{fact_id}
```

PATCH үшін `change_reason` міндетті. Әр сәтті CREATE/UPDATE бір transaction ішінде audit record және `master_data_revisions` immutable snapshot жасайды. Revision number әр resource үшін бөлек өседі; PostgreSQL advisory transaction lock параллель update race жағдайынан қорғайды.

`editor` DRAFT деректермен жұмыс істей алады, бірақ non-DRAFT verification status орнатуға әрекет жасаса HTTP `403` алады. `expert` және `admin` ғылыми verification status көтере алады; evidence/provenance талаптары бәрібір сақталады.

## Сыртқы review

Review queue тек authenticated user үшін ашық. `CONFIRM_LINK`, `REJECT_LINK`, `MANUAL_LINK`, `CREATE_DRAFT_FIELD`, сондай-ақ license record `ACCEPT/REJECT` шешімдері `expert` немесе `admin` рөлін талап етеді.

Reviewer identity **тек authenticated principal** ішінен алынады. Ескі client compatibility үшін request body ішінде `reviewer` field уақытша қабылдануы мүмкін, бірақ backend оны елемейді. Client басқа адамның атынан шешім жаза алмайды.

External record негізінде жаңа field жасалса, ол тек `DRAFT` болады. Сол transaction ішінде жаңа `GeologicalEntity` revision және review audit record жазылады. Verified `ExternalEntityLink` geological object-ті автоматты түрде `VERIFIED` етпейді.

## AuditLog

Толық audit log тек admin үшін:

```text
GET /api/v1/audit/logs
```

Фильтрлер: `action`, `resource_type`, `resource_id`, `limit`, `offset`. Audit record actor snapshot (`actor_username`, `actor_role`), action, resource type/ID, reason және technical details сақтайды.

`audit_logs` және `master_data_revisions` PostgreSQL trigger арқылы append-only. Қалыпты `UPDATE` және `DELETE` database деңгейінде reject болады. Бұл application code қатесі болған жағдайда да тарихтың үнсіз өзгертілуіне жол бермейді.

## Revision history

Кез келген authenticated user scientific master data тарихын оқи алады:

```text
GET /api/v1/audit/revisions/source/{source_id}
GET /api/v1/audit/revisions/geological_entity/{entity_id}
GET /api/v1/audit/revisions/fact/{fact_id}
```

Әр revision ішінде `revision_number`, action, өзгерістен кейінгі толық JSON snapshot, `change_reason`, actor және timestamp бар. Ескі revision-ды қалпына келтіру автоматты history rewrite болмауы тиіс; restoration жаңа explicit change және жаңа revision ретінде жазылуы қажет.

## Core Dataset

`GET /api/v1/core-dataset/status` read-only күйінде login-сыз қолжетімді. Орнату:

```text
POST /api/v1/core-dataset/install
```

тек `admin` үшін. Manifest/checksum validation міндетті болып қалады. Core Dataset user/expert verified master data-ны үнсіз overwrite етпеуі тиіс.

## Қауіпсіздік

Bearer token, password және басқа secrets Git, issue, screenshot немесе documentation ішіне салынбайды. Remote access кезінде HTTPS қолдану керек. Password CLI argument ретінде берілмейді. Бұл P0 local auth/RBAC foundation береді; SSO/OIDC, MFA, password reset және enterprise identity кейінгі жеке кезеңдерде қосылады, local offline-capable core-ды артық күрделендірмей.
