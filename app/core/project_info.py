from typing import Final, Literal, TypedDict

SupportedLanguage = Literal["ru", "kk", "en"]
SUPPORTED_LANGUAGES: Final[tuple[SupportedLanguage, ...]] = ("ru", "kk", "en")

PROJECT_NAME: Final[str] = "GeoKZ"
PROJECT_VERSION: Final[str] = "0.2.0-dev"
AUTHOR_NAME: Final[str] = "Sarmuldin Rinat"
AUTHOR_EMAIL: Final[str] = "ura07srr@gmail.com"


class LocalizedProjectInfo(TypedDict):
    title: str
    description: str


PROJECT_INFO: Final[dict[SupportedLanguage, LocalizedProjectInfo]] = {
    "ru": {
        "title": "GeoKZ — геологическая информационная система Казахстана",
        "description": (
            "Доказательная геологическая информационная система для хранения, поиска, "
            "пространственного анализа и экспертной проверки геологических знаний с "
            "прослеживаемостью до первичных и внешних источников."
        ),
    },
    "kk": {
        "title": "GeoKZ — Қазақстанның геологиялық ақпараттық жүйесі",
        "description": (
            "Геологиялық білімді сақтау, іздеу, кеңістіктік талдау және сараптамалық "
            "тексеруге арналған, бастапқы және сыртқы дереккөздерге дейінгі деректердің "
            "шығу тегін сақтайтын дәлелді геологиялық ақпараттық жүйе."
        ),
    },
    "en": {
        "title": "GeoKZ — Geological Information System of Kazakhstan",
        "description": (
            "An evidence-based geological information system for storing, searching, "
            "spatially analysing, and expert-reviewing geological knowledge with "
            "traceability to primary and external sources."
        ),
    },
}
