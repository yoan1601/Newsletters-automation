"""
Load non-secret project config from config/ at the project root.
Secrets (API keys, OAuth) stay in .env — only runtime settings live here.
"""

import json
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load(filename: str) -> dict:
    path = _CONFIG_DIR / filename
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def newsletter() -> dict:
    return _load("newsletter.json")


def brand() -> dict:
    return _load("brand.json")
