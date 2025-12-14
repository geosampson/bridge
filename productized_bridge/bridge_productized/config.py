from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path(os.environ.get("BRIDGE_CONFIG_DIR", Path.home() / ".bridge_productized"))
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class BridgeConfig:
    """Persistent configuration for WooCommerce, ERP, and licensing."""

    store_url: str
    consumer_key: str
    consumer_secret: str
    capital_base_url: str
    capital_username: str
    capital_password: str
    capital_company: int
    capital_fiscalyear: int
    capital_branch: int
    license_key: str
    customer_name: str
    update_channel: str = "stable"
    current_version: str = "0.0.0"

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> Optional["BridgeConfig"]:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return cls(**data)

    def save(self, path: Path = CONFIG_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(asdict(self), handle, indent=2)


def create_config(
    store_url: str,
    consumer_key: str,
    consumer_secret: str,
    capital_base_url: str,
    capital_username: str,
    capital_password: str,
    capital_company: int,
    capital_fiscalyear: int,
    capital_branch: int,
    license_key: str,
    customer_name: str,
    update_channel: str = "stable",
    current_version: str = "0.0.0",
    path: Path = CONFIG_FILE,
) -> BridgeConfig:
    config = BridgeConfig(
        store_url=store_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        capital_base_url=capital_base_url,
        capital_username=capital_username,
        capital_password=capital_password,
        capital_company=capital_company,
        capital_fiscalyear=capital_fiscalyear,
        capital_branch=capital_branch,
        license_key=license_key,
        customer_name=customer_name,
        update_channel=update_channel,
        current_version=current_version,
    )
    config.save(path=path)
    return config


__all__ = ["BridgeConfig", "create_config", "CONFIG_DIR", "CONFIG_FILE"]
