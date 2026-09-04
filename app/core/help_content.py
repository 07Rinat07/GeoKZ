from app.core.project_info import SupportedLanguage
from app.schemas.help import HelpLevel, HelpTopic

_HELP_TOPICS: dict[str, dict[SupportedLanguage, HelpTopic]] = {
    "coordinates.format": {
        "ru": HelpTopic(
            code="coordinates.format",
            title="Формат координат",
            short_hint="Рекомендуется ввод через точку; запятая также принимается.",
            details=(
                "Пример: 5085125.325 или 5085125,325. Для широты и долготы: "
                "43.652341 / 51.168420. Пробелы при копировании из таблиц удаляются автоматически."
            ),
            level=HelpLevel.HINT,
            language="ru",
            related_codes=["coordinates.crs"],
        ),
        "kk": HelpTopic(
            code="coordinates.format",
            title="Координаттар пішімі",
            short_hint="Нүктемен енгізу ұсынылады; үтір де қабылданады.",
            details=(
                "Мысал: 5085125.325 немесе 5085125,325. Ендік пен бойлық үшін: "
                "43.652341 / 51.168420. Кестеден көшіру кезіндегі бос орындар автоматты түрде жойылады."
            ),
            level=HelpLevel.HINT,
            language="kk",
            related_codes=["coordinates.crs"],
        ),
        "en": HelpTopic(
            code="coordinates.format",
            title="Coordinate format",
            short_hint="A decimal point is recommended; a comma is also accepted.",
            details=(
                "Example: 5085125.325 or 5085125,325. For latitude/longitude use values such as "
                "43.652341 / 51.168420. Spaces copied from spreadsheets are removed automatically."
            ),
            level=HelpLevel.HINT,
            language="en",
            related_codes=["coordinates.crs"],
        ),
    },
    "coordinates.crs": {
        "ru": HelpTopic(
            code="coordinates.crs",
            title="Система координат",
            short_hint="Большие X/Y в метрах требуют выбора исходной системы координат.",
            details=(
                "По значениям X/Y нельзя надёжно определить CRS. Укажите EPSG-код, UTM-зону, "
                "СК-42/Гаусса–Крюгера или локальную систему предприятия. GeoKZ сохраняет исходные "
                "координаты и преобразует рабочую точку в WGS84."
            ),
            level=HelpLevel.WARNING,
            language="ru",
            related_codes=["coordinates.format"],
        ),
        "kk": HelpTopic(
            code="coordinates.crs",
            title="Координаттар жүйесі",
            short_hint="Метрмен берілген үлкен X/Y мәндері бастапқы координаттар жүйесін таңдауды талап етеді.",
            details=(
                "X/Y мәндерінің өзіне қарап CRS-ті сенімді анықтау мүмкін емес. EPSG кодын, UTM аймағын, "
                "СК-42/Гаусс–Крюгерді немесе кәсіпорынның жергілікті жүйесін көрсетіңіз. GeoKZ бастапқы "
                "координаттарды сақтап, жұмыс нүктесін WGS84 жүйесіне түрлендіреді."
            ),
            level=HelpLevel.WARNING,
            language="kk",
            related_codes=["coordinates.format"],
        ),
        "en": HelpTopic(
            code="coordinates.crs",
            title="Coordinate reference system",
            short_hint="Large metric X/Y values require the source coordinate system.",
            details=(
                "A CRS cannot be identified reliably from X/Y values alone. Provide an EPSG code, UTM zone, "
                "SK-42/Gauss-Kruger definition, or a configured local company CRS. GeoKZ preserves the source "
                "coordinates and transforms the working point to WGS84."
            ),
            level=HelpLevel.WARNING,
            language="en",
            related_codes=["coordinates.format"],
        ),
    },
    "depth.reference": {
        "ru": HelpTopic(
            code="depth.reference",
            title="MD, TVD и TVDSS",
            short_hint="Всегда указывайте систему отсчёта глубины.",
            details=(
                "MD — измеренная глубина по стволу; TVD — истинная вертикальная глубина; TVDSS — вертикальная "
                "глубина относительно уровня моря. Значения нельзя сравнивать без учёта reference."
            ),
            level=HelpLevel.CONTEXT,
            language="ru",
            related_codes=["correlation.depth"],
        ),
        "kk": HelpTopic(
            code="depth.reference",
            title="MD, TVD және TVDSS",
            short_hint="Тереңдіктің есептеу жүйесін әрқашан көрсетіңіз.",
            details=(
                "MD — ұңғыма оқпаны бойымен өлшенген тереңдік; TVD — шынайы тік тереңдік; TVDSS — теңіз "
                "деңгейіне қатысты тік тереңдік. Reference ескерілмей мәндерді салыстыруға болмайды."
            ),
            level=HelpLevel.CONTEXT,
            language="kk",
            related_codes=["correlation.depth"],
        ),
        "en": HelpTopic(
            code="depth.reference",
            title="MD, TVD and TVDSS",
            short_hint="Always specify the depth reference.",
            details=(
                "MD is measured depth along the wellbore; TVD is true vertical depth; TVDSS is vertical depth "
                "relative to mean sea level. Values should not be compared without the reference."
            ),
            level=HelpLevel.CONTEXT,
            language="en",
            related_codes=["correlation.depth"],
        ),
    },
    "well.logs": {
        "ru": HelpTopic(
            code="well.logs",
            title="ГИС / каротаж",
            short_hint="GeoKZ хранит запуск, интервалы, кривые, единицы и исходный файл раздельно.",
            details=(
                "Для LAS/DLIS/WITSML сохраняются исходный mnemonic, единицы, диапазон глубин, способ получения, "
                "источник и checksum. Интерпретация хранится отдельно от исходного измерения."
            ),
            level=HelpLevel.CONTEXT,
            language="ru",
            related_codes=["correlation.marker"],
        ),
        "kk": HelpTopic(
            code="well.logs",
            title="ҰГЗ / каротаж",
            short_hint="GeoKZ өлшеу сеансын, интервалдарды, қисықтарды, бірліктерді және бастапқы файлды бөлек сақтайды.",
            details=(
                "LAS/DLIS/WITSML үшін бастапқы mnemonic, өлшем бірлігі, тереңдік аралығы, алу әдісі, дереккөз "
                "және checksum сақталады. Интерпретация бастапқы өлшемнен бөлек сақталады."
            ),
            level=HelpLevel.CONTEXT,
            language="kk",
            related_codes=["correlation.marker"],
        ),
        "en": HelpTopic(
            code="well.logs",
            title="Well logs",
            short_hint="GeoKZ keeps the run, intervals, curves, units and source file separately.",
            details=(
                "For LAS/DLIS/WITSML, GeoKZ preserves the original mnemonic, units, depth range, acquisition "
                "method, source and checksum. Interpretation is stored separately from the raw measurement."
            ),
            level=HelpLevel.CONTEXT,
            language="en",
            related_codes=["correlation.marker"],
        ),
    },
    "correlation.marker": {
        "ru": HelpTopic(
            code="correlation.marker",
            title="Репер в корреляции",
            short_hint="Репер — узнаваемая стратиграфическая или геофизическая отметка для сопоставления скважин.",
            details=(
                "GeoKZ хранит код и название репера, глубину, метод интерпретации, источник, достоверность и "
                "статус проверки. Автоматическая линия корреляции должна быть прослеживаема до этих данных."
            ),
            level=HelpLevel.CONTEXT,
            language="ru",
            related_codes=["correlation.depth", "well.logs"],
        ),
        "kk": HelpTopic(
            code="correlation.marker",
            title="Корреляциядағы репер",
            short_hint="Репер — ұңғымаларды салыстыруға қолданылатын танылатын стратиграфиялық немесе геофизикалық белгі.",
            details=(
                "GeoKZ репер кодын/атауын, тереңдігін, интерпретация әдісін, дереккөзін, сенімділігін және "
                "тексеру мәртебесін сақтайды. Автоматты корреляциялық сызық осы деректерге дейін қадағалануы тиіс."
            ),
            level=HelpLevel.CONTEXT,
            language="kk",
            related_codes=["correlation.depth", "well.logs"],
        ),
        "en": HelpTopic(
            code="correlation.marker",
            title="Correlation marker",
            short_hint="A marker is a recognizable stratigraphic or geophysical pick used to correlate wells.",
            details=(
                "GeoKZ stores the marker code/name, depth, interpretation method, source, confidence and "
                "verification status. An automatic correlation line must remain traceable to this evidence."
            ),
            level=HelpLevel.CONTEXT,
            language="en",
            related_codes=["correlation.depth", "well.logs"],
        ),
    },
    "correlation.depth": {
        "ru": HelpTopic(
            code="correlation.depth",
            title="Система глубин при корреляции",
            short_hint="Для соседних скважин предпочтительно сравнивать реперы по TVDSS.",
            details=(
                "TVDSS позволяет сравнивать вертикальные отметки относительно общего уровня. MD зависит от "
                "траектории ствола. Если системы глубин несовместимы, GeoKZ предупреждает и не строит ложную линию."
            ),
            level=HelpLevel.WARNING,
            language="ru",
            related_codes=["depth.reference", "correlation.marker"],
        ),
        "kk": HelpTopic(
            code="correlation.depth",
            title="Корреляция кезіндегі тереңдік жүйесі",
            short_hint="Көршілес ұңғымалар үшін реперлерді TVDSS бойынша салыстырған дұрыс.",
            details=(
                "TVDSS ортақ деңгейге қатысты тік белгілерді салыстыруға мүмкіндік береді. MD ұңғыма "
                "траекториясына тәуелді. Тереңдік жүйелері үйлеспесе, GeoKZ ескерту көрсетіп, жалған сызық құрмайды."
            ),
            level=HelpLevel.WARNING,
            language="kk",
            related_codes=["depth.reference", "correlation.marker"],
        ),
        "en": HelpTopic(
            code="correlation.depth",
            title="Depth reference for correlation",
            short_hint="TVDSS is preferred when comparing markers between nearby wells.",
            details=(
                "TVDSS compares vertical positions against a common datum, while MD depends on wellbore "
                "trajectory. If depth references are incompatible, GeoKZ warns the user and avoids a false line."
            ),
            level=HelpLevel.WARNING,
            language="en",
            related_codes=["depth.reference", "correlation.marker"],
        ),
    },
    "data.provenance": {
        "ru": HelpTopic(
            code="data.provenance",
            title="Откуда взялись данные",
            short_hint="У каждого важного значения должен быть источник и статус проверки.",
            details=(
                "GeoKZ показывает документ/API, дату получения, страницу или интервал, исходное значение, "
                "статус верификации и возможные противоречия с другими источниками."
            ),
            level=HelpLevel.CONTEXT,
            language="ru",
        ),
        "kk": HelpTopic(
            code="data.provenance",
            title="Деректер қайдан алынған",
            short_hint="Әр маңызды мәннің дереккөзі және тексеру мәртебесі болуы керек.",
            details=(
                "GeoKZ құжатты/API-ды, алынған күнін, бетті немесе интервалды, бастапқы мәнді, тексеру "
                "мәртебесін және басқа дереккөздермен қайшылықтарды көрсетеді."
            ),
            level=HelpLevel.CONTEXT,
            language="kk",
        ),
        "en": HelpTopic(
            code="data.provenance",
            title="Data provenance",
            short_hint="Every important value should have a source and verification status.",
            details=(
                "GeoKZ shows the document/API, retrieval date, page or interval, original value, verification "
                "status and any conflicts with other sources."
            ),
            level=HelpLevel.CONTEXT,
            language="en",
        ),
    },
}


def get_help_topics(language: SupportedLanguage) -> list[HelpTopic]:
    return [translations[language] for translations in _HELP_TOPICS.values()]


def get_help_topic(code: str, language: SupportedLanguage) -> HelpTopic | None:
    translations = _HELP_TOPICS.get(code)
    if translations is None:
        return None
    return translations[language]
