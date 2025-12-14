from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

DEFAULT_MANIFEST_URL = os.environ.get("BRIDGE_MANIFEST_URL", "https://updates.example.com/bridge/manifest.json")
DOWNLOAD_DIR = Path(os.environ.get("BRIDGE_DOWNLOAD_DIR", Path.home() / ".bridge_productized" / "downloads"))


@dataclass
class UpdateManifest:
    version: str
    download_url: str
    notes: str


def fetch_manifest(manifest_url: str = DEFAULT_MANIFEST_URL, timeout: int = 5) -> Optional[UpdateManifest]:
    try:
        response = requests.get(manifest_url, timeout=timeout)
    except requests.RequestException:
        return None
    if response.status_code != 200:
        return None
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return None
    if not all(key in payload for key in ("version", "download_url", "notes")):
        return None
    return UpdateManifest(
        version=str(payload["version"]),
        download_url=str(payload["download_url"]),
        notes=str(payload["notes"]),
    )


def is_newer_version(current: str, candidate: str) -> bool:
    def parse(version: str) -> tuple[int, ...]:
        return tuple(int(part) for part in version.split("."))

    current_parts = parse(current)
    candidate_parts = parse(candidate)
    return candidate_parts > current_parts


def download_update(manifest: UpdateManifest) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = DOWNLOAD_DIR / f"bridge_{manifest.version}.zip"
    with requests.get(manifest.download_url, stream=True, timeout=10) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    handle.write(chunk)
    return target


def check_for_updates(current_version: str) -> Optional[Path]:
    manifest = fetch_manifest()
    if manifest is None:
        return None
    if not is_newer_version(current_version, manifest.version):
        return None
    return download_update(manifest)


__all__ = [
    "UpdateManifest",
    "fetch_manifest",
    "download_update",
    "is_newer_version",
    "check_for_updates",
    "DEFAULT_MANIFEST_URL",
    "DOWNLOAD_DIR",
]
