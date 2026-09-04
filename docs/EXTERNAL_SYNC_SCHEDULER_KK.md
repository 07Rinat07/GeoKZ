# GeoKZ — сыртқы синхрондау scheduler-і (KK)

## Мақсаты

GeoKZ рұқсат етілген сыртқы дереккөздерді негізгі FastAPI request processing-тен бөлек синхрондайды. Периодтық scheduler жеке process/container ретінде іске қосылады және әр API worker ішінде background loop құрмайды. Бұл API масштабталғанда duplicate sync туындауына жол бермейді.

Негізгі схема:

```text
GeoKZ API / PySide6
        |
        +--> POST /api/v1/integrations/sync-all       # қолмен «Барлығын жаңарту»
        |
        +--> GET  /api/v1/integrations/scheduler/status

Dedicated scheduler process
        |
        +--> ExternalSyncCoordinator.sync_due()
        |
        +--> PostgreSQL source reservation
        |
        +--> connector -> RAW/staging -> checksum/diff
```

## Іске қосу режимдері

### Қолмен «Барлығын жаңарту»

```text
POST /api/v1/integrations/sync-all
```

Команда GeoKZ connector-ы бар барлық enabled source-тарды синхрондауға әрекет етеді. `enabled=false` source өткізіледі. Егер нақты source қазірдің өзінде синхрондалып жатса, бүкіл batch тоқтамайды: сол source үшін `ALREADY_RUNNING` қайтарылады, ал қалғандары жалғасады.

### Тек due source-тарды жоспарлы іске қосу

```text
POST /api/v1/integrations/scheduler/run-due
```

Бұл endpoint dedicated scheduler process қолданатын алгоритмді диагностика немесе қолмен тексеру үшін шақырады. Production-та оны бірнеше cron немесе FastAPI worker-ден қатар шақыру қажет емес.

Scheduler тек `sync_mode=AUTOMATIC` source-тарды тексереді. Әр source үшін оның `sync_interval_hours` мәні қолданылады.

### Scheduler күйі

```text
GET /api/v1/integrations/scheduler/status
```

Жауапта:

- `poll_seconds` — scheduler process тексеру жиілігі;
- `failure_retry_hours` — соңғы қатеден кейінгі retry аралығы;
- `running_timeout_hours` — stale `RUNNING` шегі;
- `sources[]` — әр source күйі;
- `next_due_at` және `due`;
- белсенді sync болса `running_run_id`;
- соңғы successful sync және соңғы error көрсетіледі.

## Қатар іске қосылудан қорғау

Жаңа `ExternalSyncRun(status=RUNNING)` жасалмас бұрын GeoKZ PostgreSQL арқылы `external_data_sources` жолын қысқа уақытқа `SELECT ... FOR UPDATE` арқылы lock етеді.

Critical section тек run reservation қамтиды:

1. source row lock;
2. ағымдағы `RUNNING` іздеу;
3. тым ескі `RUNNING` жазбаларын `FAILED` ету;
4. жаңа `RUNNING` жасау;
5. commit және lock босату.

Сыртқы HTTP transfer row lock ұстамай орындалады. Сондықтан баяу provider басқа source-тарға немесе status read-қа ұзақ DB lock тудырмайды.

Екінші sync белсенді run кезінде келсе, `ExternalSyncAlreadyRunningError` қайтарылады. Бір source sync REST endpoint-і оны HTTP `409` ретінде береді.

## Stale RUNNING recovery

Process авариялық тоқтағанда `RUNNING` жабылмай қалуы мүмкін. GeoKZ оны мәңгілік lock деп есептемейді.

Порог:

```env
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

Келесі reservation кезінде `started_at` осы шектен ескі `RUNNING` жазбалары диагностикалық `error_message` арқылы `FAILED` күйіне ауысады. Содан кейін жаңа run бастала алады.

## Due/retry саясаты

History жоқ жаңа `AUTOMATIC` source бірден `due=true` болады.

Success кейін:

```text
next_due_at = last_success_at + sync_interval_hours
```

Егер соңғы error соңғы success-тен кейін болса:

```text
next_due_at = last_error_at + min(sync_interval_hours, failure_retry_hours)
```

Retry source-тың қалыпты sync interval-ынан сирек болмайды.

`MANUAL` және disabled source-тар үшін scheduled `next_due_at` болмайды.

## Batch status

`sync-all` және `run-due` жалпы summary және әр source үшін жеке result қайтарады.

Негізгі `dispatch_status` мәндері:

- `SUCCESS` — sync аяқталды;
- `FAILED` — connector/config/provider error;
- `ALREADY_RUNNING` — source басқа run-мен бос емес;
- `SKIPPED_NOT_DUE` — жоспарлы batch-та мерзімі келмеген;
- `SKIPPED_DISABLED` — source disabled;
- `SKIPPED_MANUAL` — source scheduled due режиміне кірмейді;
- `SKIPPED_UNSUPPORTED` — source тіркелген, бірақ connector factory әлі жоқ.

Бір source қатесі басқа source-тарды batch ішінде тоқтатпайды.

## Docker Compose

`docker compose up --build` үш process іске қосады:

```text
geokz-db
geokz-api
geokz-external-sync-scheduler
```

Scheduler healthy API-ды күтеді, содан кейін:

```text
python -m scripts.external_sync_scheduler
```

Бір реттік тексеру:

```text
python -m scripts.external_sync_scheduler --once
```

## Баптаулар

`.env`:

```env
GEOKZ_EXTERNAL_SCHEDULER_POLL_SECONDS=300
GEOKZ_EXTERNAL_SYNC_FAILURE_RETRY_HOURS=6
GEOKZ_EXTERNAL_SYNC_RUNNING_TIMEOUT_HOURS=6
```

`poll_seconds` source `sync_interval_hours` мәнін өзгертпейді. Ол worker `next_due_at` келді ме деп қаншалықты жиі тексеретінін ғана анықтайды.

## API key және offline behavior

Scheduler сыртқы API-ды GeoKZ үшін міндетті runtime dependency етпейді. `GEOKZ_EGOV_API_KEY` жоқ болса да local DB, search, passports және review жұмысын жалғастырады. eGov sync әрекеті per-source error ретінде жазылады, scheduler process тірі қалады.

API key REST payload, GeoKZ URL, UI storage немесе Git ішінде сақталмауы керек. Ол тек runtime environment арқылы оқылады.

## Жауапкершілік шекарасы

Scheduler тек RAW/staging жазбаларын қауіпсіз алуға және sync history жүргізуге жауап береді. Ол geological fact-тарды растамайды және master data өзгерістерін жарияламайды.

Sync кейін normalization -> matching -> human review бөлек орындалады. Verified GeoKZ facts scheduler арқылы автоматты түрде өзгертілмейді.
