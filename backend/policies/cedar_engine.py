"""
PRAAPTI AI - Local Cedar Policy Evaluation Engine
Evaluates statutory RTI drafting & scheme access permissions using Cedar policy language.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("praapti.cedar_engine")
logging.basicConfig(level=logging.INFO)

@dataclass
class AuthDecision:
    decision: str  # "ALLOW" or "DENY"
    principal: str
    action: str
    resource: str
    reason: str
    diagnostics: Dict[str, Any]

class CedarEngine:
    """
    Local Cedar authorization evaluation wrapper.
    Supports cedarpy native bindings with robust fallback evaluation for local development.
    """

    def __init__(self, policy_path: Optional[str] = None):
        self.policy_path = policy_path or os.getenv(
            "CEDAR_POLICY_PATH", 
            os.path.join(os.path.dirname(__file__), "auth.cedar")
        )
        self.policy_content = self._load_policy()
        self._cedarpy_available = False

        try:
            import cedarpy  # type: ignore
            self._cedarpy = cedarpy
            self._cedarpy_available = True
            logger.info("Native cedarpy engine loaded successfully.")
        except ImportError:
            logger.warning(
                "cedarpy package not installed. Operating in Local Python Cedar Rule Engine mode."
            )

    def _load_policy(self) -> str:
        """Reads Cedar policy definition from disk."""
        try:
            with open(self.policy_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Cedar policy file not found at {self.policy_path}")
            return ""

    def evaluate(
        self,
        principal: Dict[str, Any],
        action: str,
        resource: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> AuthDecision:
        """
        Evaluate an authorization request against loaded Cedar policies.

        Args:
            principal: Dict containing 'id', 'type', 'is_verified', 'kyc_level', 'roles'
            action: Action identifier, e.g. "Action::DraftTier1RTI", "Action::DraftTier3CICAppeal"
            resource: Dict containing 'id', 'type', 'attributes'
            context: Additional request context (e.g. timestamp, ip_address)
        """
        # Normalize action name
        clean_action = action.replace("Action::", "").strip('"')
        principal_id = principal.get("id", "Citizen::anonymous")
        resource_id = resource.get("id", "Resource::RTIApplication")
        is_verified = principal.get("is_verified", False)
        kyc_level = principal.get("kyc_level", "unverified")
        roles = principal.get("roles", [])

        # 1. Native cedarpy path if available
        if self._cedarpy_available:
            try:
                request = {
                    "principal": f"User::\"{principal_id}\"",
                    "action": f"Action::\"{clean_action}\"",
                    "resource": f"Resource::\"{resource_id}\"",
                    "context": context or {}
                }
                entities = [
                    {
                        "uid": {"type": "User", "id": principal_id},
                        "attrs": {
                            "is_verified": is_verified,
                            "kyc_level": kyc_level
                        },
                        "parents": [{"type": "Role", "id": r} for r in roles]
                    },
                    {
                        "uid": {"type": "Resource", "id": resource_id},
                        "attrs": resource.get("attributes", {}),
                        "parents": []
                    }
                ]
                result = self._cedarpy.is_authorized(
                    request, self.policy_content, entities
                )
                decision_str = "ALLOW" if result.decision.name.lower() == "allow" else "DENY"
                return AuthDecision(
                    decision=decision_str,
                    principal=principal_id,
                    action=clean_action,
                    resource=resource_id,
                    reason=f"Cedar policy evaluation: {decision_str}",
                    diagnostics={"engine": "cedarpy_native", "details": str(result.diagnostics)}
                )
            except Exception as e:
                logger.error(f"Native cedar evaluation error: {e}. Falling back to rule engine.")

        # 2. Local Cedar Rule Engine Fallback (Guaranteed to run 100% locally)
        return self._local_evaluate(principal_id, is_verified, kyc_level, roles, clean_action, resource_id)

    def _local_evaluate(
        self,
        principal_id: str,
        is_verified: bool,
        kyc_level: str,
        roles: list,
        action: str,
        resource_id: str
    ) -> AuthDecision:
        """
        Implements the exact logic specified in auth.cedar:
        - Public discovery: Always ALLOW
        - Tier 1 & 2 RTI: ALLOW if is_verified == True
        - Tier 3 CIC Appeal: FORBID if is_verified == False, ALLOW if verified + valid KYC
        - Auditor actions: ALLOW if role == Auditor
        """
        # Public scheme discovery actions
        if action in ["SearchSchemes", "ViewSchemeDetails", "CheckEligibility"]:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Public welfare scheme discovery is open to all citizens.",
                diagnostics={"policy_rule": "Rule 1", "engine": "local_cedar_runtime"}
            )

        # Tier 3 CIC Second Appeal - Explicit Forbid if unverified
        if action == "DraftTier3CICAppeal":
            if not is_verified:
                return AuthDecision(
                    decision="DENY",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason="FORBIDDEN: Tier 3 Central Information Commission (CIC) Second Appeals require verified KYC (Aadhaar OTP / DigiLocker).",
                    diagnostics={"policy_rule": "Rule 4 (forbid)", "engine": "local_cedar_runtime"}
                )
            if kyc_level in ["aadhaar_otp", "digilocker", "offline_kyc"]:
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason="Permitted: Verified citizen with authenticated KYC level.",
                    diagnostics={"policy_rule": "Rule 3", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Denied: Insufficient KYC tier for statutory CIC Second Appeal drafting.",
                diagnostics={"policy_rule": "Default Deny", "engine": "local_cedar_runtime"}
            )

        # Tier 1 (PIO) & Tier 2 (FAA) RTIs
        if action in ["DraftTier1RTI", "DraftTier2RTI"]:
            if is_verified:
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason=f"Permitted: Verified citizen authorized to draft {action}.",
                    diagnostics={"policy_rule": "Rule 2", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"Denied: Citizen verification required to draft statutory {action}.",
                diagnostics={"policy_rule": "Rule 2 (Requirement Not Met)", "engine": "local_cedar_runtime"}
            )

        # Auditor actions
        if action in ["AuditRTIHistory", "ExportRTIArchive"] and "Auditor" in roles:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Principal possesses Auditor role.",
                diagnostics={"policy_rule": "Rule 5", "engine": "local_cedar_runtime"}
            )

        # Default Deny
        return AuthDecision(
            decision="DENY",
            principal=principal_id,
            action=action,
            resource=resource_id,
            reason="Denied: No matching Cedar permit policy for this request.",
            diagnostics={"policy_rule": "Default Deny", "engine": "local_cedar_runtime"}
        )

# Module instance for direct imports
cedar_engine = CedarEngine()

if __name__ == "__main__":
    # Self-test scenarios
    print("=== Testing Cedar Engine Local Evaluation ===")
    
    # 1. Unverified user requesting Tier 3 CIC Appeal (Should be DENY)
    res1 = cedar_engine.evaluate(
        principal={"id": "citizen_101", "is_verified": False, "kyc_level": "unverified"},
        action="DraftTier3CICAppeal",
        resource={"id": "rti_cic_001"}
    )
    print(f"Test 1 [Unverified Tier 3]: {res1.decision} -> {res1.reason}")
    assert res1.decision == "DENY"

    # 2. Verified user requesting Tier 1 RTI (Should be ALLOW)
    res2 = cedar_engine.evaluate(
        principal={"id": "citizen_102", "is_verified": True, "kyc_level": "aadhaar_otp"},
        action="DraftTier1RTI",
        resource={"id": "rti_tier1_002"}
    )
    print(f"Test 2 [Verified Tier 1]: {res2.decision} -> {res2.reason}")
    assert res2.decision == "ALLOW"

    # 3. Verified user requesting Tier 3 CIC Appeal (Should be ALLOW)
    res3 = cedar_engine.evaluate(
        principal={"id": "citizen_103", "is_verified": True, "kyc_level": "digilocker"},
        action="DraftTier3CICAppeal",
        resource={"id": "rti_cic_003"}
    )
    print(f"Test 3 [Verified Tier 3]: {res3.decision} -> {res3.reason}")
    assert res3.decision == "ALLOW"
    print("=== All Cedar Engine tests passed! ===")
