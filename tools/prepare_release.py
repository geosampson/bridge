from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from productized_bridge.bridge_productized.license_manager import LicenseManager

PUBLIC_MANIFEST = Path("productized_bridge/public_manifest.json")


def write_manifest(version: str, download_url: str, notes: str) -> Path:
    payload = {"version": version, "download_url": download_url, "notes": notes}
    PUBLIC_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return PUBLIC_MANIFEST


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare public manifest or issue a license key")
    parser.add_argument("--version")
    parser.add_argument("--download-url")
    parser.add_argument("--notes", default="")
    parser.add_argument("--issue-license")
    parser.add_argument("--expires")
    parser.add_argument("--feature", action="append", default=[])
    args = parser.parse_args()

    if args.issue_license:
        expires = args.expires or date.today().replace(year=date.today().year + 1).isoformat()
        features = {flag: True for flag in args.feature}
        manager = LicenseManager()
        key = manager.issue_license(customer=args.issue_license, expires=expires, features=features)
        print(key)
        return

    if not args.version or not args.download_url:
        raise SystemExit("Provide --version and --download-url or use --issue-license")
    manifest_path = write_manifest(version=args.version, download_url=args.download_url, notes=args.notes)
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
