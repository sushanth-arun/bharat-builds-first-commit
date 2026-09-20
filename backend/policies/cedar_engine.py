"""
PRAAPTI AI - Advanced Cedar Policy Evaluation Engine
Evaluates statutory RTI drafting, fee waivers, emergency access & zero-trust policies using Cedar policy language.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
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
    Advanced Cedar authorization evaluation engine wrapper.
    Supports cedarpy native bindings with robust, high-precision fallback evaluation for local development.
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
                "cedarpy package not installed. Operating in Advanced Local Cedar Rule Engine mode."
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
            principal: Dict containing 'id', 'is_verified', 'kyc_level', 'is_bpl', 'age', 'disability_status', 'account_status', 'roles', 'department'
            action: Action identifier, e.g. "Action::DraftTier1RTI", "Action::DraftTier3CICAppeal", "Action::ClaimRTIFeeExemption"
            resource: Dict containing 'id', 'type', 'tier', 'department', 'is_life_or_liberty', 'contains_pii', 'attributes'
            context: Additional request context (e.g. 'is_emergency', 'daily_rti_count', 'ip_address')
        """
        clean_action = action.replace("Action::", "").strip('"')
        principal_id = principal.get("id", "Citizen::anonymous")
        resource_id = resource.get("id", "Resource::RTIApplication")
        context_data = context or {}

        # 1. Native cedarpy path if available
        if self._cedarpy_available:
            try:
                request = {
                    "principal": f"User::\"{principal_id}\"",
                    "action": f"Action::\"{clean_action}\"",
                    "resource": f"Resource::\"{resource_id}\"",
                    "context": context_data
                }
                entities = [
                    {
                        "uid": {"type": "User", "id": principal_id},
                        "attrs": {
                            "is_verified": principal.get("is_verified", False),
                            "kyc_level": principal.get("kyc_level", "unverified"),
                            "is_bpl": principal.get("is_bpl", False),
                            "age": principal.get("age", 30),
                            "disability_status": principal.get("disability_status", False),
                            "account_status": principal.get("account_status", "active"),
                            "department": principal.get("department", "")
                        },
                        "parents": [{"type": "Role", "id": r} for r in principal.get("roles", ["Citizen"])]
                    },
                    {
                        "uid": {"type": "Resource", "id": resource_id},
                        "attrs": {
                            "department": resource.get("department", ""),
                            "is_life_or_liberty": resource.get("is_life_or_liberty", False),
                            "contains_pii": resource.get("contains_pii", False),
                            "tier": resource.get("tier", "")
                        },
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
                    reason=f"Native Cedar policy evaluation: {decision_str}",
                    diagnostics={"engine": "cedarpy_native", "details": str(result.diagnostics)}
                )
            except Exception as e:
                logger.error(f"Native cedar evaluation error: {e}. Falling back to rule engine.")

        # 2. Advanced Local Cedar Engine Fallback (Guaranteed 100% statutory execution)
        return self._local_evaluate(principal, clean_action, resource, context_data)

    def _local_evaluate(
        self,
        principal: Dict[str, Any],
        action: str,
        resource: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AuthDecision:
        """
        Faithfully evaluates the 14-rule Cedar policy hierarchy:
        - FORBID rules strictly override PERMIT rules.
        - PERMIT rules grant explicit access.
        - Default DENY if no permit rule matches.
        """
        principal_id = principal.get("id", "Citizen::anonymous")
        resource_id = resource.get("id", "Resource::RTIApplication")

        is_verified = principal.get("is_verified", False)
        kyc_level = principal.get("kyc_level", "unverified")
        is_bpl = principal.get("is_bpl", False)
        age = principal.get("age", 30)
        disability_status = principal.get("disability_status", False)
        account_status = principal.get("account_status", "active")
        roles = principal.get("roles", ["Citizen"])
        principal_dept = principal.get("department", "")

        resource_dept = resource.get("department", "")
        is_life_or_liberty = resource.get("is_life_or_liberty", False)
        contains_pii = resource.get("contains_pii", False)

        is_emergency = context.get("is_emergency", False)
        daily_rti_count = context.get("daily_rti_count", 0)

        # Normalize action aliases
        action_map = {
            "tier1": "DraftTier1RTI", "TIER1": "DraftTier1RTI",
            "tier2": "DraftTier2RTI", "TIER2": "DraftTier2RTI",
            "tier3": "DraftTier3CICAppeal", "TIER3": "DraftTier3CICAppeal"
        }
        action = action_map.get(action, action)

        # ----------------------------------------------------------------------
        # PHASE 1: FORBID RULES EVALUATION (FORBID OVERRIDES ALL PERMITS)
        # ----------------------------------------------------------------------

        # Rule 7: FORBID Suspended, Blacklisted, or Bot-flagged Accounts from legal RTI drafting
        if account_status in ["suspended", "blacklisted", "flagged_bot"] and action in [
            "DraftTier1RTI", "DraftTier2RTI", "DraftTier3CICAppeal", "DraftUrgentLifeLibertyRTI", "ClaimRTIFeeExemption"
        ]:
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"FORBIDDEN: Account status is '{account_status}'. Statutory RTI operations are prohibited for flagged accounts.",
                diagnostics={"policy_rule": "Rule 7 (Forbid)", "engine": "local_cedar_runtime"}
            )

        # Rule 8: FORBID Unverified Accounts from Tier 3 Second Appeals
        if action == "DraftTier3CICAppeal" and not is_verified:
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="FORBIDDEN: Tier 3 Central Information Commission (CIC) Appeals require verified identity (Aadhaar OTP / DigiLocker).",
                diagnostics={"policy_rule": "Rule 8 (Forbid)", "engine": "local_cedar_runtime"}
            )

        # Rule 9: FORBID Abuse of Emergency 48-Hour Life/Liberty Route by Unverified Users
        if action == "DraftUrgentLifeLibertyRTI" and (not is_verified or kyc_level == "unverified"):
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="FORBIDDEN: Emergency 48-Hour Life or Liberty RTI drafting requires authenticated citizen identity.",
                diagnostics={"policy_rule": "Rule 9 (Forbid)", "engine": "local_cedar_runtime"}
            )

        # Rule 10: FORBID Daily Volume Limit Exceeded (Anti-Spam Rate Limit)
        if daily_rti_count >= 10 and action in [
            "DraftTier1RTI", "DraftTier2RTI", "DraftTier3CICAppeal", "DraftUrgentLifeLibertyRTI"
        ] and "SuperUser" not in roles and "SystemAdmin" not in roles:
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"FORBIDDEN: Daily statutory RTI submission limit exceeded ({daily_rti_count}/10 max). Rate limit enforced.",
                diagnostics={"policy_rule": "Rule 10 (Forbid)", "engine": "local_cedar_runtime"}
            )

        # Rule 14: FORBID Unredacted PII Export for Non-Admins / Non-Auditors
        if action in ["ExportRawCitizenPII", "ViewUnredactedAadhaar"] and contains_pii:
            if not ("SystemAdmin" in roles or "Auditor" in roles):
                return AuthDecision(
                    decision="DENY",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason="FORBIDDEN: Data Privacy Safeguard prohibits unredacted PII export for non-administrative roles.",
                    diagnostics={"policy_rule": "Rule 14 (Forbid)", "engine": "local_cedar_runtime"}
                )

        # ----------------------------------------------------------------------
        # PHASE 2: PERMIT RULES EVALUATION
        # ----------------------------------------------------------------------

        # Rule 13: System Administrator Full Administrative Access
        if "SystemAdmin" in roles:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Principal possesses SystemAdmin full administrative role.",
                diagnostics={"policy_rule": "Rule 13", "engine": "local_cedar_runtime"}
            )

        # Rule 1: Public Welfare Scheme Discovery & Guidance
        if action in ["SearchSchemes", "ViewSchemeDetails", "CheckEligibility", "ExportSchemeGuide"]:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Public welfare scheme discovery and guidance is open to all citizens.",
                diagnostics={"policy_rule": "Rule 1", "engine": "local_cedar_runtime"}
            )

        # Rule 2: Anti-Scam Phishing & Fraud Reporting
        if action in ["FlagSuspiciousScheme", "ReportPhishingDomain"]:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Anti-scam phishing reporting is open to all citizens.",
                diagnostics={"policy_rule": "Rule 2", "engine": "local_cedar_runtime"}
            )

        # Rule 3: Tier 1 (PIO) & Tier 2 (FAA) RTIs
        if action in ["DraftTier1RTI", "DraftTier2RTI"]:
            if is_verified and account_status == "active":
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason=f"Permitted: Verified citizen authorized to draft statutory {action}.",
                    diagnostics={"policy_rule": "Rule 3", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"Denied: Citizen identity verification and active account status required for {action}.",
                diagnostics={"policy_rule": "Rule 3 (Requirement Not Met)", "engine": "local_cedar_runtime"}
            )

        # Rule 4: Tier 3 CIC / SIC Second Appeal
        if action == "DraftTier3CICAppeal":
            if is_verified and account_status == "active" and kyc_level in ["aadhaar_otp", "digilocker", "offline_kyc"]:
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason=f"Permitted: Verified citizen with authenticated high-trust KYC level ({kyc_level}).",
                    diagnostics={"policy_rule": "Rule 4", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"Denied: High-trust KYC (Aadhaar/DigiLocker) required for statutory CIC Second Appeals.",
                diagnostics={"policy_rule": "Rule 4 (Requirement Not Met)", "engine": "local_cedar_runtime"}
            )

        # Rule 5: Statutory Fee Exemption Claims (RTI Act Sec 7(5))
        if action == "ClaimRTIFeeExemption":
            if is_verified and (is_bpl or age >= 60 or disability_status):
                exemption_grounds = []
                if is_bpl: exemption_grounds.append("BPL Household Status")
                if age >= 60: exemption_grounds.append(f"Senior Citizen ({age} yrs)")
                if disability_status: exemption_grounds.append("Divyangjan (PwD)")
                
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason=f"Permitted: Statutory RTI application fee waiver granted under Section 7(5) for {', '.join(exemption_grounds)}.",
                    diagnostics={"policy_rule": "Rule 5", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Denied: Statutory fee exemption requires verified BPL card, Senior Citizen status (60+ yrs), or PwD certification.",
                diagnostics={"policy_rule": "Rule 5 (Requirement Not Met)", "engine": "local_cedar_runtime"}
            )

        # Rule 6: Emergency Life or Liberty 48-Hour RTI (RTI Act Sec 7(1) Proviso)
        if action == "DraftUrgentLifeLibertyRTI":
            if is_verified and account_status == "active" and (is_emergency or is_life_or_liberty):
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason="Permitted: Expedited 48-Hour Life or Liberty RTI application authorized under Section 7(1) Proviso of RTI Act 2005.",
                    diagnostics={"policy_rule": "Rule 6", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Denied: Expedited 48-Hour RTI drafting requires verified identity and urgent life/liberty grounds.",
                diagnostics={"policy_rule": "Rule 6 (Requirement Not Met)", "engine": "local_cedar_runtime"}
            )

        # Rule 11: Auditor Access
        if action in ["AuditRTIHistory", "InspectAnonymizedLogs", "ExportRTIArchive"] and "Auditor" in roles:
            return AuthDecision(
                decision="ALLOW",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason="Permitted: Principal possesses certified Auditor role.",
                diagnostics={"policy_rule": "Rule 11", "engine": "local_cedar_runtime"}
            )

        # Rule 12: Public Information Officer (PIO) Official Intake
        if action in ["InspectCitizenGrievance", "VerifyApplicantKYC", "UpdateRTIStatus"] and "PIO_Officer" in roles:
            if resource_dept and principal_dept and resource_dept.lower() == principal_dept.lower():
                return AuthDecision(
                    decision="ALLOW",
                    principal=principal_id,
                    action=action,
                    resource=resource_id,
                    reason=f"Permitted: PIO Officer authorized for department '{resource_dept}'.",
                    diagnostics={"policy_rule": "Rule 12", "engine": "local_cedar_runtime"}
                )
            return AuthDecision(
                decision="DENY",
                principal=principal_id,
                action=action,
                resource=resource_id,
                reason=f"Denied: PIO Officer departmental jurisdiction mismatch (Officer: '{principal_dept}', Resource: '{resource_dept}').",
                diagnostics={"policy_rule": "Rule 12 (Jurisdiction Mismatch)", "engine": "local_cedar_runtime"}
            )

        # ----------------------------------------------------------------------
        # PHASE 3: DEFAULT DENY
        # ----------------------------------------------------------------------
        return AuthDecision(
            decision="DENY",
            principal=principal_id,
            action=action,
            resource=resource_id,
            reason="Denied: No matching Cedar permit policy for this authorization request.",
            diagnostics={"policy_rule": "Default Deny", "engine": "local_cedar_runtime"}
        )

# Module instance for direct imports
cedar_engine = CedarEngine()

if __name__ == "__main__":
    print("=" * 80)
    print("PRAAPTI AI - Advanced Cedar Policy Engine (Statutory Self-Test Suite)")
    print("=" * 80)
    
    # Test 1: Unverified user requesting Tier 3 CIC Appeal (Should be DENY via Rule 8 Forbid)
    res1 = cedar_engine.evaluate(
        principal={"id": "citizen_101", "is_verified": False, "kyc_level": "unverified"},
        action="DraftTier3CICAppeal",
        resource={"id": "rti_cic_001"}
    )
    print(f"Test 1 [Unverified Tier 3]: {res1.decision} -> {res1.reason}")
    assert res1.decision == "DENY"

    # Test 2: Verified user requesting Tier 1 RTI (Should be ALLOW via Rule 3)
    res2 = cedar_engine.evaluate(
        principal={"id": "citizen_102", "is_verified": True, "kyc_level": "aadhaar_otp", "account_status": "active"},
        action="DraftTier1RTI",
        resource={"id": "rti_tier1_002"}
    )
    print(f"Test 2 [Verified Tier 1]: {res2.decision} -> {res2.reason}")
    assert res2.decision == "ALLOW"

    # Test 3: Verified BPL Citizen claiming Fee Exemption (Should be ALLOW via Rule 5)
    res3 = cedar_engine.evaluate(
        principal={"id": "citizen_103", "is_verified": True, "is_bpl": True, "age": 35},
        action="ClaimRTIFeeExemption",
        resource={"id": "rti_fee_003"}
    )
    print(f"Test 3 [BPL Fee Waiver]: {res3.decision} -> {res3.reason}")
    assert res3.decision == "ALLOW"

    # Test 4: Senior Citizen (65 yrs) claiming Fee Exemption (Should be ALLOW via Rule 5)
    res4 = cedar_engine.evaluate(
        principal={"id": "citizen_104", "is_verified": True, "is_bpl": False, "age": 65},
        action="ClaimRTIFeeExemption",
        resource={"id": "rti_fee_004"}
    )
    print(f"Test 4 [Senior Citizen Fee Waiver]: {res4.decision} -> {res4.reason}")
    assert res4.decision == "ALLOW"

    # Test 5: Suspended Account attempting RTI (Should be DENY via Rule 7 Forbid)
    res5 = cedar_engine.evaluate(
        principal={"id": "citizen_105", "is_verified": True, "account_status": "suspended"},
        action="DraftTier1RTI",
        resource={"id": "rti_tier1_005"}
    )
    print(f"Test 5 [Suspended Account Forbid]: {res5.decision} -> {res5.reason}")
    assert res5.decision == "DENY"

    # Test 6: Urgent Life/Liberty 48-Hour RTI (Should be ALLOW via Rule 6)
    res6 = cedar_engine.evaluate(
        principal={"id": "citizen_106", "is_verified": True, "kyc_level": "aadhaar_otp", "account_status": "active"},
        action="DraftUrgentLifeLibertyRTI",
        resource={"id": "rti_urgent_006", "is_life_or_liberty": True},
        context={"is_emergency": True}
    )
    print(f"Test 6 [Emergency 48-Hr RTI]: {res6.decision} -> {res6.reason}")
    assert res6.decision == "ALLOW"

    # Test 7: Rate Limit Exceeded (12 RTIs today) (Should be DENY via Rule 10 Forbid)
    res7 = cedar_engine.evaluate(
        principal={"id": "citizen_107", "is_verified": True, "account_status": "active"},
        action="DraftTier1RTI",
        resource={"id": "rti_tier1_007"},
        context={"daily_rti_count": 12}
    )
    print(f"Test 7 [Rate Limit Forbid]: {res7.decision} -> {res7.reason}")
    assert res7.decision == "DENY"

    # Test 8: Data Privacy Safeguard - PII export by regular citizen (Should be DENY via Rule 14 Forbid)
    res8 = cedar_engine.evaluate(
        principal={"id": "citizen_108", "is_verified": True, "roles": ["Citizen"]},
        action="ExportRawCitizenPII",
        resource={"id": "db_pii_008", "contains_pii": True}
    )
    print(f"Test 8 [PII Privacy Safeguard]: {res8.decision} -> {res8.reason}")
    assert res8.decision == "DENY"

    print("=" * 80)
    print("=== All 8 Advanced Cedar Engine statutory tests passed successfully! ===")
    print("=" * 80)

