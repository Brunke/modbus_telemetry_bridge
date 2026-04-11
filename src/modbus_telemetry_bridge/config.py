from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .mapping import TagMapping


def _resolve_secret(section: dict[str, Any], key: str) -> str | None:
    if key in section and section[key] is not None:
        return str(section[key])

    env_key = section.get(f"{key}_env")
    if env_key:
        return os.getenv(str(env_key))

    return None


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        cfg = json.load(fh)

    influx = cfg.get("influxdb", {})
    if influx:
        influx["token"] = _resolve_secret(influx, "token")

    mqtt = cfg.get("mqtt", {})
    if mqtt:
        mqtt["username"] = _resolve_secret(mqtt, "username")
        mqtt["password"] = _resolve_secret(mqtt, "password")

    return cfg


def load_mappings(cfg: dict[str, Any]) -> list[TagMapping]:
    return [TagMapping.from_dict(item) for item in cfg.get("tags", [])]
