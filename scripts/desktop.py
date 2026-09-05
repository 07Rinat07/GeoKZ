from __future__ import annotations

import argparse

from app.desktop.localization import DesktopLanguage
from app.desktop.qt import run_desktop


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GeoKZ PySide6 desktop client")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="GeoKZ API base URL",
    )
    parser.add_argument(
        "--lang",
        choices=("ru", "kk", "en"),
        default="ru",
        help="Initial desktop language",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    language: DesktopLanguage = args.lang
    return run_desktop(default_base_url=args.api_url, language=language)


if __name__ == "__main__":
    raise SystemExit(main())
