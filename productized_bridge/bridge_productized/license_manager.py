from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

LICENSE_SECRET_ENV = "BRIDGE_LICENSE_SECRET"


@dataclass
class LicensePayload:
    customer: str
    expires: str
    features: Dict[str, bool]

    @property
    def expires_at(self) -> datetime:
        return datetime.fromisoformat(self.expires)


class LicenseManager:
    def __init__(self, signing_secret: str | None = None) -> None:
        self.signing_secret = signing_secret or os.environ.get(LICENSE_SECRET_ENV, "")

    def _sign(self, payload: str) -> str:
        digest = hmac.new(self.signing_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8")

    def issue_license(self, customer: str, expires: str, features: Dict[str, bool] | None = None) -> str:
        features = features or {}
        payload_dict = {"customer": customer, "expires": expires, "features": features}
        payload = base64.urlsafe_b64encode(json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")).decode("utf-8")
        signature = self._sign(payload)
        return f"{payload}.{signature}"

    def validate_license(self, license_key: str) -> LicensePayload:
        if not self.signing_secret:
            raise ValueError("Missing signing secret. Set BRIDGE_LICENSE_SECRET.")
        try:
            payload_b64, signature = license_key.split(".", maxsplit=1)
        except ValueError as exc:
            raise ValueError("Invalid license format") from exc
        expected_signature = self._sign(payload_b64)
        if not hmac.compare_digest(expected_signature, signature):
            raise ValueError("Invalid license signature")
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
        payload_data = json.loads(payload_json)
        payload = LicensePayload(**payload_data)
        if datetime.utcnow() > payload.expires_at:
            raise ValueError("License expired")
        return payload


__all__ = ["LicenseManager", "LicensePayload", "LICENSE_SECRET_ENV"]
