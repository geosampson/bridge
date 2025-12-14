from __future__ import annotations

from pathlib import Path

from .config import BridgeConfig, CONFIG_FILE
from .license_manager import LicenseManager
from .update_service import check_for_updates


class BridgeProductizedApp:
    def __init__(self, config_path: Path = CONFIG_FILE) -> None:
        config = BridgeConfig.load(config_path)
        if config is None:
            raise SystemExit("Configuration not found. Run the setup wizard first: python -m bridge_productized.setup_wizard")
        self.config = config
        self.license_manager = LicenseManager()

    def ensure_license(self) -> None:
        payload = self.license_manager.validate_license(self.config.license_key)
        print(f"License valid for {payload.customer} until {payload.expires}")

    def check_updates(self) -> None:
        downloaded = check_for_updates(self.config.current_version)
        if downloaded:
            print(f"New version downloaded to {downloaded}. Please apply the update before continuing.")

    def run(self) -> None:
        self.ensure_license()
        self.check_updates()
        print("BRIDGE productized wrapper initialized. Launch your existing bridge_app.py build here.")


if __name__ == "__main__":
    app = BridgeProductizedApp()
    app.run()
