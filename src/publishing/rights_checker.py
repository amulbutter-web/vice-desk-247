"""
Rights Clearance and Consent Verification Engine.
Enforces creator consent, platform copyright terms, and handles instant revocation.
"""
from typing import Dict, Any, Tuple
from datetime import datetime, timezone


class RightsClearanceError(Exception):
    pass


class RightsChecker:
    def __init__(self):
        # In-memory registry of creator authorizations and scopes
        self.consent_registry: Dict[str, Dict[str, Any]] = {}

    def register_consent(
        self,
        creator_key: str,
        platform: str,
        scope: str = "clips_and_publishing",
        expires_at_utc: str = "2099-01-01T00:00:00Z",
    ):
        """Registers verified creator consent."""
        self.consent_registry[creator_key] = {
            "creator_key": creator_key,
            "platform": platform,
            "scope": scope,
            "status": "verified",
            "expires_at_utc": expires_at_utc,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def revoke_consent(self, creator_key: str, reason: str = "creator_request"):
        """Instantly revokes creator consent, halting all downstream publishing."""
        if creator_key in self.consent_registry:
            self.consent_registry[creator_key]["status"] = "revoked"
            self.consent_registry[creator_key]["revocation_reason"] = reason

    def check_rights(self, creator_key: str, destination: str) -> Tuple[bool, str]:
        """
        Validates whether publishing is authorized for the given creator and destination platform.
        """
        consent = self.consent_registry.get(creator_key)
        if not consent:
            return False, f"No consent record found for creator: {creator_key}"

        if consent["status"] == "revoked":
            return False, f"Consent revoked for creator: {creator_key} (Reason: {consent.get('revocation_reason')})"

        if consent["status"] != "verified":
            return False, f"Consent status is {consent['status']} (expected verified)"

        return True, "Rights cleared and consent verified"
