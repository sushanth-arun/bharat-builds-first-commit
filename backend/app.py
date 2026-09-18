"""
PRAAPTI AI - Main Strands Agents SDK Application
Civic Intelligence Platform for Indian Welfare Schemes & Statutory RTI Drafting.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import local engines and utilities
from policies.cedar_engine import cedar_engine, AuthDecision
from search.scheme_indexer import scheme_indexer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("praapti.agent")

# Optional Strands SDK decorator wrapper (falls back gracefully if running in local standalone mode)
try:
    from strands import Agent, tool  # type: ignore
except ImportError:
    # Lightweight tool decorator stub for 100% local development
    def tool(func):
        func.__is_tool__ = True
        return func

    class Agent:
        def __init__(self, name: str, description: str, tools: list):
            self.name = name
            self.description = description
            self.tools = {t.__name__: t for t in tools}
            logger.info(f"Initialized Local Agent '{self.name}' with {len(self.tools)} tools.")

        def run(self, action: str, **kwargs):
            if action in self.tools:
                return self.tools[action](**kwargs)
            raise ValueError(f"Unknown tool/action: {action}")


# -----------------------------------------------------------------------------
# Agent Tools
# -----------------------------------------------------------------------------

@tool
def search_welfare_schemes(
    query: str = "",
    category: Optional[str] = None,
    annual_income: Optional[int] = None,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Searches and filters central & state welfare schemes based on citizen eligibility criteria.
    """
    logger.info(f"Executing search_welfare_schemes tool: query='{query}', category='{category}'")
    schemes = scheme_indexer.search_schemes(
        query=query,
        category=category,
        annual_income=annual_income,
        gender=gender,
        age=age,
        limit=limit
    )
    return {
        "status": "success",
        "total_matched": len(schemes),
        "schemes": schemes
    }


@tool
def evaluate_rti_authorization(
    citizen_id: str,
    tier: str,
    is_verified: bool = False,
    kyc_level: str = "unverified"
) -> Dict[str, Any]:
    """
    Evaluates Cedar authorization policies before permitting RTI draft generation.
    - Tier 1: Initial RTI under Section 6(1) to Public Information Officer (PIO)
    - Tier 2: First Appeal under Section 19(1) to First Appellate Authority (FAA)
    - Tier 3: Second Appeal under Section 19(3) to Central/State Information Commission (CIC/SIC)
    """
    action_map = {
        "tier1": "DraftTier1RTI",
        "tier2": "DraftTier2RTI",
        "tier3": "DraftTier3CICAppeal"
    }

    cedar_action = action_map.get(tier.lower(), "DraftTier1RTI")
    decision: AuthDecision = cedar_engine.evaluate(
        principal={"id": citizen_id, "is_verified": is_verified, "kyc_level": kyc_level},
        action=cedar_action,
        resource={"id": f"RTIApplication::{tier.upper()}"}
    )

    return {
        "citizen_id": citizen_id,
        "requested_tier": tier.upper(),
        "action": cedar_action,
        "decision": decision.decision,  # "ALLOW" or "DENY"
        "reason": decision.reason,
        "diagnostics": decision.diagnostics
    }


@tool
def draft_rti_application(
    applicant_name: str,
    applicant_address: str,
    public_authority: str,
    department: str,
    tier: str = "tier1",
    scheme_or_matter: str = "",
    specific_queries: List[str] = None,
    is_verified: bool = False,
    kyc_level: str = "unverified"
) -> Dict[str, Any]:
    """
    Statutorily drafts an RTI Application adhering to Right to Information Act, 2005 formatting rules.
    Runs Cedar authorization check first.
    """
    if specific_queries is None:
        specific_queries = []

    # 1. Evaluate Cedar Policy
    auth_check = evaluate_rti_authorization(
        citizen_id=applicant_name,
        tier=tier,
        is_verified=is_verified,
        kyc_level=kyc_level
    )

    if auth_check["decision"] != "ALLOW":
        return {
            "status": "error",
            "error_code": "CEDAR_AUTH_DENIED",
            "message": auth_check["reason"],
            "auth_details": auth_check
        }

    # 2. Format Statutory RTI Draft
    current_date = datetime.now().strftime("%d %B, %Y")
    formatted_queries = "\n".join([f"  {idx+1}. {q}" for idx, q in enumerate(specific_queries)])

    if tier.lower() == "tier1":
        draft_text = f"""FORM 'A' - APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005

To,
The Public Information Officer (PIO) / Assistant Public Information Officer (APIO),
Department: {department}
Public Authority: {public_authority}

1. Full Name of the Applicant: {applicant_name}
2. Address for Correspondence: {applicant_address}
3. Subject Matter: Request for official records/status regarding: {scheme_or_matter}

4. Particulars of Information Required:
{formatted_queries}

5. Statutory Timeline:
   Under Section 7(1) of the RTI Act 2005, the requested information must be furnished within 30 days (or 48 hours if concerning Life or Liberty).

6. Application Fee:
   Prescribed fee of ₹10/- enclosed via IPO / Demand Draft / Online Portal Receipt. (Citizens below poverty line are exempt under Section 7(5)).

Declaration:
I am a citizen of India and hereby declare that the information sought does not fall under exemptions of Section 8 or 9 of the RTI Act 2005.

Date: {current_date}
Signature of Applicant: {applicant_name}
"""
    elif tier.lower() == "tier2":
        draft_text = f"""FIRST APPEAL MEMORANDUM UNDER SECTION 19(1) OF THE RIGHT TO INFORMATION ACT, 2005

To,
The First Appellate Authority (FAA),
Department: {department}
Public Authority: {public_authority}

1. Appellant Name: {applicant_name}
2. Address: {applicant_address}
3. Details of PIO against whose order/inaction appeal is preferred: PIO, {department}, {public_authority}
4. Matter of Appeal: First appeal against non-receipt/unsatisfactory response for matter: {scheme_or_matter}

5. Grounds for Appeal:
{formatted_queries}

6. Prayer / Relief Sought:
   The FAA is requested to direct the PIO to supply certified copies of the requested information without further delay and invoke Section 20 penalties if applicable.

Date: {current_date}
Appellant Signature: {applicant_name}
"""
    else:  # tier3 CIC appeal
        draft_text = f"""SECOND APPEAL MEMORANDUM BEFORE THE CENTRAL/STATE INFORMATION COMMISSION UNDER SECTION 19(3) OF RTI ACT 2005

To,
The Registrar / Hon'ble Information Commissioner,
Central Information Commission (CIC) / State Information Commission (SIC),

In the Matter of:
{applicant_name} (Appellant)
Vs.
1. PIO, {department}, {public_authority} (Respondent 1)
2. First Appellate Authority (FAA), {department} (Respondent 2)

Statutory Verification: Verified Citizen [{kyc_level.upper()}]
Subject: Second Appeal regarding non-compliance in matter: {scheme_or_matter}

Points of Law & Grounds for Second Appeal:
{formatted_queries}

Relief Claimed:
1. Imposition of maximum penalty of ₹25,000 under Section 20(1) on the errant PIO.
2. Recommendation for disciplinary proceedings under Section 20(2).
3. Award of compensation under Section 19(8)(b) to the Appellant.

Date: {current_date}
Appellant Signature: {applicant_name}
"""

    return {
        "status": "success",
        "tier": tier.upper(),
        "applicant": applicant_name,
        "department": department,
        "draft_content": draft_text,
        "cedar_authorization": auth_check
    }


@tool
def check_fraud_alert(url_or_text: str) -> Dict[str, Any]:
    """
    Scans a domain, URL, or scheme claim against known fraudulent phishing patterns.
    """
    fraud_file = os.path.join(os.path.dirname(__file__), "data/fraud_patterns.json")
    if os.path.exists(fraud_file):
        with open(fraud_file, "r", encoding="utf-8") as f:
            patterns = json.load(f)
    else:
        patterns = {"suspicious_domains": [], "legitimate_tlds": [".gov.in", ".nic.in"]}

    flagged_issues = []
    is_suspicious = False

    for s_dom in patterns.get("suspicious_domains", []):
        if s_dom.lower() in url_or_text.lower():
            is_suspicious = True
            flagged_issues.append(f"Domain matches known malicious phishing database entry: '{s_dom}'")

    if ("pm" in url_or_text.lower() or "yojana" in url_or_text.lower()) and not any(tld in url_or_text.lower() for tld in patterns.get("legitimate_tlds", [])):
        if "http" in url_or_text.lower() or ".com" in url_or_text.lower() or ".org" in url_or_text.lower():
            is_suspicious = True
            flagged_issues.append("Scheme claims government identity but lacks legitimate '.gov.in' or '.nic.in' domain suffix.")

    for red_flag in patterns.get("phishing_red_flags", []):
        keywords = red_flag.lower().split()
        if any(kw in url_or_text.lower() for kw in ["upi", "qr code", "registration fee", "lottery", "instant cash"]):
            flagged_issues.append(f"Detected suspicious pattern: {red_flag}")
            is_suspicious = True
            break

    return {
        "input_scanned": url_or_text,
        "is_safe": not is_suspicious,
        "risk_level": "HIGH_RISK" if is_suspicious else "SAFE",
        "flagged_issues": flagged_issues
    }


# -----------------------------------------------------------------------------
# Strands Agent Instantiation
# -----------------------------------------------------------------------------

praapti_agent = Agent(
    name="PRAAPTI_Civic_Agent",
    description="Lead Civic Intelligence Assistant for Indian Welfare Schemes & RTI Drafting",
    tools=[
        search_welfare_schemes,
        evaluate_rti_authorization,
        draft_rti_application,
        check_fraud_alert
    ]
)

if __name__ == "__main__":
    print("================================================================")
    print(" PRAAPTI AI - Civic Intelligence & RTI Assistant (Agent Runtime)")
    print("================================================================\n")

    # Demo 1: Search Schemes for a low-income farmer
    print("1. [Agent Tool] Searching Welfare Schemes for Farmer:")
    schemes_res = search_welfare_schemes(query="farmer", category="Agriculture", annual_income=150000)
    print(f"-> Found {schemes_res['total_matched']} matching schemes.")
    for s in schemes_res["schemes"]:
        print(f"   - {s['title']} ({s['scheme_id']})")

    # Demo 2: Cedar Auth Deny on Unverified Tier 3 CIC Appeal
    print("\n2. [Agent Tool] Cedar Policy Check: Unverified Citizen requesting Tier 3 CIC Appeal:")
    deny_auth = evaluate_rti_authorization("citizen_ramesh", tier="tier3", is_verified=False)
    print(f"-> Decision: {deny_auth['decision']} | Reason: {deny_auth['reason']}")

    # Demo 3: Draft Tier 1 RTI for Verified Citizen
    print("\n3. [Agent Tool] Drafting Tier 1 RTI Application (Verified Citizen):")
    rti_res = draft_rti_application(
        applicant_name="Ramesh Kumar",
        applicant_address="Village Ramgarh, Dist. Gorakhpur, UP",
        public_authority="District Agriculture Office",
        department="Department of Agriculture & Farmers Welfare",
        tier="tier1",
        scheme_or_matter="Non-disbursement of PM-KISAN 16th installment",
        specific_queries=[
            "Provide daily progress report on Application Ref #UP-KISAN-982103.",
            "Certified copy of reasons recorded for withholding DBT transfer.",
            "Name and designation of the dealing officer responsible for clearance."
        ],
        is_verified=True,
        kyc_level="aadhaar_otp"
    )
    print(f"-> Status: {rti_res['status']}")
    print("-> Generated Draft Preview:\n" + "\n".join(rti_res["draft_content"].split("\n")[:10]) + "\n...")

    # Demo 4: Fraud Detection
    print("\n4. [Agent Tool] Fraud Pattern Detection:")
    fraud_res = check_fraud_alert("http://pm-kisan-yojna.org/pay-registration-fee-via-upi")
    print(f"-> Risk Level: {fraud_res['risk_level']} | Issues: {fraud_res['flagged_issues']}")
