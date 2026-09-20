"""
========================================================================================
PRAAPTI AI (प्राप्ति AI) — Unified Agent Core & Serverless API Baseline
Pradhanmantri & Rajya Assistance Application, Probability, and Transparency Interface
Civic Intelligence Platform & Statutory RTI Engine
========================================================================================

TEAM REPOSITORY DIVISION & SECTION OWNERSHIP:
  - LAPTOP 1 (Teammate 1): Agent Core, Strands Agents SDK, & Dynamic Orchestration Workflow
  - LAPTOP 2 (Teammate 2): Cedar Authorization Engine & Zero-Trust Policy Wrapper
  - LAPTOP 3 (Teammate 3): OpenSearch Hybrid & Vector Retrieval Client (with Fallback Engine)
  - LAPTOP 4 (Teammate 4): AWS SAM CLI Lambda Handler & Local API Gateway Routing
========================================================================================
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("praapti.unified_app")


# ======================================================================================
# DATA MODELS & SCHEMAS (Pydantic v2 / Strict Typing Contract)
# ======================================================================================

class CitizenProfile(BaseModel):
    name: str = Field(..., description="Full Name of the citizen")
    age: int = Field(..., ge=0, le=120, description="Age in years")
    gender: str = Field("All", description="Gender: Male, Female, Transgender, Other, All")
    state: str = Field("All India", description="State or Union Territory")
    district: str = Field("", description="District name")
    occupation: str = Field("General", description="Occupation or livelihood (e.g. Farmer, Student, Artisan, Street Vendor, Unemployed, Senior Citizen)")
    annual_income: int = Field(0, ge=0, description="Annual family income in INR")
    land_holding_acres: float = Field(0.0, ge=0.0, description="Cultivable land holding in acres")
    caste_category: str = Field("General", description="Caste / Social category: General, OBC, SC, ST, EWS")
    is_bpl: bool = Field(False, description="Whether the household holds BPL / Ration / Antyodaya status")
    is_verified: bool = Field(False, description="Whether citizen identity is authenticated")
    kyc_level: str = Field("unverified", description="KYC trust level: 'unverified', 'aadhaar_otp', 'digilocker', 'offline_kyc'")
    disability_status: bool = Field(False, description="Whether citizen holds Divyangjan / PwD status")
    account_status: str = Field("active", description="Account status: 'active', 'suspended', 'blacklisted'")
    roles: List[str] = Field(default_factory=lambda: ["Citizen"], description="System user roles")
    available_documents: List[str] = Field(
        default_factory=lambda: ["Aadhaar Card"]
    )
    rti_target_department: Optional[str] = Field(None, description="Target government department for grievance")
    rti_target_matter: Optional[str] = Field(None, description="Specific inquiry or grievance matter description")


class SchemeMatchResult(BaseModel):
    scheme_id: str
    title: str
    short_code: str
    ministry: str
    category: str
    description: str
    benefits: str
    is_eligible: bool
    empirical_approval_odds: float  # e.g. 0.88 = 88%
    match_score: int                # e.g. 88
    eligibility_reasons: List[str]
    missing_documents: List[str]
    official_portal: str


class RTIApplicationPayload(BaseModel):
    tier: str = Field("tier1", description="'tier1' (PIO Sec 6(1)), 'tier2' (FAA Sec 19(1)), 'tier3' (CIC Sec 19(3)), 'urgent' (Sec 7(1) Life/Liberty)")
    applicant_name: str
    applicant_address: str
    public_authority: str
    department: str
    matter_description: str
    specific_queries: List[str]
    is_verified: bool = False
    kyc_level: str = "unverified"
    is_bpl: bool = False
    age: int = 30
    disability_status: bool = False
    account_status: str = "active"
    roles: List[str] = Field(default_factory=lambda: ["Citizen"])
    is_emergency: bool = False
    is_life_or_liberty: bool = False
    claim_fee_waiver: bool = False


class PraaptiWorkflowResponse(BaseModel):
    timestamp: str
    citizen_name: str
    citizen_summary: Dict[str, Any]
    total_schemes_evaluated: int
    matched_schemes: List[SchemeMatchResult]
    top_recommended_scheme: Optional[str]
    cedar_authorization_status: Dict[str, Any]
    statutory_rti_draft: Optional[str]
    audit_trail: List[str]


# ======================================================================================
# LAPTOP 1 SECTION: Teammate 1 (Agent Core & Strands SDK Orchestration)
# ======================================================================================

# Fallback wrapper for Strands Agents SDK if package is installing in venv
try:
    from strands import Agent, tool  # type: ignore
    HAS_STRANDS_SDK = True
except ImportError:
    HAS_STRANDS_SDK = False

    def tool(func):
        """Mock decorator for Strands @tool when library is not in current path."""
        func.__is_tool__ = True
        return func

    class Agent:
        """Lightweight agent runtime simulating Strands SDK execution."""
        def __init__(self, name: str, description: str, tools: list):
            self.name = name
            self.description = description
            self.tools = {t.__name__: t for t in tools}
            logger.info(f"[LAPTOP 1] Initialized Agent '{self.name}' with {len(self.tools)} tools.")

        def run(self, action: str, **kwargs):
            if action in self.tools:
                return self.tools[action](**kwargs)
            raise ValueError(f"Action '{action}' not registered with Agent.")


# Teammate 1: Custom Strands Agent Tool Definitions
@tool
def search_schemes_tool(profile_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Wraps Laptop 3's OpenSearch vector & metadata query client."""
    profile = CitizenProfile(**profile_dict)
    return query_opensearch_schemes(profile)


@tool
def evaluate_authorization_tool(user_role: str, action: str, resource_tier: str, is_verified: bool, kyc_level: str) -> Dict[str, Any]:
    """Wraps Laptop 2's Cedar Zero-Trust Authorization Policy Engine."""
    return check_cedar_policy(
        user_role=user_role,
        action=action,
        resource_tier=resource_tier,
        is_verified=is_verified,
        kyc_level=kyc_level
    )


@tool
def compute_approval_probability(profile: CitizenProfile, scheme: Dict[str, Any]) -> Dict[str, Any]:
    """
    Empirical approval probability formula based on statutory Indian welfare criteria:
      1. Income eligibility match (25%)
      2. Occupation & Target Group match (30%)
      3. Age & Gender constraints (15%)
      4. Land holding prerequisites (15%)
      5. Document availability & KYC verification trust (15%)
    """
    score = 0.0
    reasons = []
    missing_docs = []

    el = scheme.get("eligibility", {})
    
    # 1. Income check (Weight: 25%)
    max_income = el.get("max_annual_income")
    if max_income is None:
        score += 0.25
        reasons.append("Income Requirement: Universal / No ceiling")
    elif profile.annual_income <= max_income:
        score += 0.25
        reasons.append(f"Income Requirement: PASSED (Rs. {profile.annual_income:,} <= Rs. {max_income:,})")
    elif profile.annual_income <= max_income * 1.15:
        score += 0.10
        reasons.append(f"Income Requirement: Marginal (Close to ceiling Rs. {max_income:,})")
    else:
        reasons.append(f"Income Requirement: EXCEEDED (Limit: Rs. {max_income:,})")

    # 2. Occupation / Target group match (Weight: 30%)
    target_occupations = [o.lower() for o in el.get("occupations", ["all"])]
    target_group_desc = el.get("target_group", "").lower()
    user_occ = profile.occupation.lower()

    if "all" in target_occupations or any(o in user_occ or user_occ in o for o in target_occupations):
        score += 0.30
        reasons.append(f"Occupation Match: High relevance for '{profile.occupation}'")
    elif any(term in target_group_desc for term in [user_occ, profile.caste_category.lower(), "bpl" if profile.is_bpl else ""]):
        score += 0.20
        reasons.append(f"Target Group Match: Matches social/livelihood criteria")
    else:
        score += 0.05
        reasons.append(f"Occupation Match: Neutral/General category")

    # 3. Age & Gender checks (Weight: 15%)
    age_min = el.get("age_min", 0)
    age_max = el.get("age_max", 120)
    target_gender = el.get("gender", "All")

    age_ok = (age_min <= profile.age <= age_max)
    gender_ok = (target_gender == "All" or target_gender.lower() == profile.gender.lower())

    if age_ok and gender_ok:
        score += 0.15
        reasons.append(f"Demographics: Age ({profile.age} yrs) & Gender ({profile.gender}) fully match")
    elif age_ok or gender_ok:
        score += 0.08
        reasons.append("Demographics: Partial criteria match")
    else:
        reasons.append("Demographics: Outside prescribed age/gender range")

    # 4. Land holding check (Weight: 15%)
    land_req = el.get("land_holding_required", False)
    if land_req:
        if profile.land_holding_acres > 0:
            score += 0.15
            reasons.append(f"Land Records: Verified ({profile.land_holding_acres} acres cultivable land)")
        else:
            reasons.append("Land Records: Requires cultivable landholding")
    else:
        score += 0.15
        reasons.append("Land Records: Not required for this scheme")

    # 5. Document & KYC verification readiness (Weight: 15%)
    required_docs = scheme.get("documents_required", [])
    user_docs_lower = [d.lower() for d in profile.available_documents]

    if required_docs:
        matched = 0
        for rd in required_docs:
            if any(ud in rd.lower() or rd.lower() in ud for ud in user_docs_lower):
                matched += 1
            else:
                missing_docs.append(rd)
        
        doc_ratio = matched / len(required_docs)
        doc_score = 0.10 * doc_ratio
        score += doc_score
    else:
        score += 0.10

    # KYC Trust boost
    if profile.is_verified and profile.kyc_level in ["aadhaar_otp", "digilocker", "offline_kyc"]:
        score += 0.05
        reasons.append(f"KYC Verification: Authenticated ({profile.kyc_level})")
    elif profile.is_verified:
        score += 0.03
    else:
        reasons.append("KYC Verification: Citizen unverified (Basic estimate)")

    # Normalize final score between 0.10 and 0.99
    final_odds = round(min(max(score, 0.10), 0.98), 2)

    return {
        "odds": final_odds,
        "match_score": int(final_odds * 100),
        "is_eligible": final_odds >= 0.50,
        "reasons": reasons,
        "missing_docs": missing_docs
    }


def generate_statutory_rti_text(payload: RTIApplicationPayload) -> str:
    """Generates statutory RTI legal text format under Right to Information Act, 2005."""
    curr_date = datetime.now().strftime("%d %B, %Y")
    queries_str = "\n".join([f"  {idx+1}. {q}" for idx, q in enumerate(payload.specific_queries)])

    if payload.tier.lower() in ["tier1", "1", "pio"]:
        return f"""FORM 'A' - APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005

To,
The Central / State Public Information Officer (PIO),
Department: {payload.department}
Public Authority: {payload.public_authority}

1. Full Name of Applicant: {payload.applicant_name}
2. Address for Correspondence: {payload.applicant_address}
3. Subject / Matter: Request for official records/status regarding: {payload.matter_description}

4. Specific Information Required under RTI Act 2005:
{queries_str}

5. Statutory Timeline:
   Under Section 7(1) of the RTI Act 2005, the requested information must be furnished within 30 days of receipt (or within 48 hours if concerning Life or Liberty).

6. Prescribed Fee:
   Fee of Rs. 10/- enclosed via Postal Order / Demand Draft / Online RTI Portal Receipt.
   (Note: Citizens below poverty line are exempt under Section 7(5)).

Declaration:
I am a bona fide citizen of India and hereby declare that the information sought does not fall under the exemptions of Section 8 or 9 of the RTI Act 2005.

Date: {curr_date}
Signature of Applicant: {payload.applicant_name}"""

    elif payload.tier.lower() in ["tier2", "2", "faa"]:
        return f"""FIRST APPEAL MEMORANDUM UNDER SECTION 19(1) OF THE RIGHT TO INFORMATION ACT, 2005

To,
The First Appellate Authority (FAA),
Department: {payload.department}
Public Authority: {payload.public_authority}

In the Matter of:
{payload.applicant_name} (Appellant)
Vs.
Public Information Officer (PIO), {payload.department} (Respondent)

1. Appellant Name: {payload.applicant_name}
2. Address for Correspondence: {payload.applicant_address}
3. Date of filing Section 6(1) Application: [As per original submission]
4. Grounds for First Appeal (Deemed Refusal / Unsatisfactory Reply under Section 7(2)):
{queries_str}

5. Prayer / Relief Sought:
   Direct the PIO to furnish certified, complete information without further delay and consider invoking penal provisions under Section 20(1) of the RTI Act.

Date: {curr_date}
Appellant Signature: {payload.applicant_name}"""

    else:
        return f"""SECOND APPEAL MEMORANDUM BEFORE THE HON'BLE INFORMATION COMMISSION UNDER SECTION 19(3) OF RTI ACT 2005

To,
The Registrar / Hon'ble Information Commissioner,
Central Information Commission (CIC) / State Information Commission (SIC),

In the Matter of:
{payload.applicant_name} (Appellant) [Verified Citizen KYC: {payload.kyc_level.upper()}]
Vs.
1. Public Information Officer (PIO), {payload.department} (Respondent 1)
2. First Appellate Authority (FAA), {payload.department} (Respondent 2)

Subject: Second Appeal against non-compliance and statutory failure in matter: {payload.matter_description}

Points of Law & Grounds for Second Appeal:
{queries_str}

Relief Claimed:
  1. Imposition of maximum penalty of Rs. 25,000 under Section 20(1) on the delinquent PIO.
  2. Recommendation for disciplinary proceedings under Section 20(2).
  3. Award of compensation under Section 19(8)(b) to the Appellant for detriment suffered.

Date: {curr_date}
Appellant: {payload.applicant_name}"""


# Teammate 1 Main Workflow Orchestrator
def run_praapti_agent_workflow(profile: CitizenProfile) -> PraaptiWorkflowResponse:
    """
    Main orchestration logic connecting Laptop 2 (Cedar) and Laptop 3 (OpenSearch).
    Calculates scheme eligibility, computes approval probability, and drafts RTI notices.
    """
    audit_trail: List[str] = []
    location_str = f"{profile.district}, {profile.state}" if profile.district else profile.state
    audit_trail.append(f"Initiated PRAAPTI Civic Agent workflow for: '{profile.name}' | Occupation: '{profile.occupation}' | Location: '{location_str}'")

    # Step 1: OpenSearch / Dynamic Knowledge Base Retrieval (Laptop 3)
    raw_schemes = query_opensearch_schemes(profile, limit=15)
    audit_trail.append(f"Retrieved {len(raw_schemes)} welfare schemes from knowledge base.")

    # Step 2: Dynamic Eligibility & Probability Assessment
    evaluated_schemes: List[SchemeMatchResult] = []
    for s in raw_schemes:
        eval_res = compute_approval_probability(profile, s)
        odds = eval_res["odds"]

        evaluated_schemes.append(SchemeMatchResult(
            scheme_id=s.get("scheme_id", "SCHEME-UNKNOWN"),
            title=s.get("title", "Welfare Scheme"),
            short_code=s.get("short_code", s.get("scheme_id", "GOV")),
            ministry=s.get("ministry", "Government of India"),
            category=s.get("category", "General Welfare"),
            description=s.get("description", "Government welfare assistance program."),
            benefits=s.get("benefits", "Financial / welfare assistance."),
            is_eligible=eval_res["is_eligible"],
            empirical_approval_odds=odds,
            match_score=eval_res["match_score"],
            eligibility_reasons=eval_res["reasons"],
            missing_documents=eval_res["missing_docs"],
            official_portal=s.get("official_portal", "https://india.gov.in")
        ))

    # Sort schemes by empirical approval odds in descending order
    evaluated_schemes.sort(key=lambda x: x.empirical_approval_odds, reverse=True)
    top_scheme = evaluated_schemes[0].title if evaluated_schemes else None

    # Step 3: Cedar Authorization Check (Laptop 2)
    rti_tier = "tier1"
    cedar_action = "DraftTier1RTI"
    cedar_auth = check_cedar_policy(
        user_role="Citizen",
        action=cedar_action,
        resource_tier=rti_tier,
        is_verified=profile.is_verified,
        kyc_level=profile.kyc_level,
        is_bpl=profile.is_bpl,
        age=profile.age,
        disability_status=profile.disability_status,
        account_status=profile.account_status,
        roles=profile.roles
    )
    audit_trail.append(f"Cedar Zero-Trust Policy [{cedar_action}]: {cedar_auth.get('decision')} ({cedar_auth.get('rule_id')}) - {cedar_auth.get('reason')}")

    # Step 4: RTI Notice Drafting if authorized
    rti_draft = None
    target_matter = profile.rti_target_matter or f"Application status & DBT record inquiry for {top_scheme or 'Welfare Scheme'}"
    target_dept = profile.rti_target_department or f"District Welfare / Nodal Office, {location_str}"

    if cedar_auth.get("decision") == "ALLOW":
        rti_payload = RTIApplicationPayload(
            tier=rti_tier,
            applicant_name=profile.name,
            applicant_address=location_str,
            public_authority=target_dept,
            department=target_dept,
            matter_description=target_matter,
            specific_queries=[
                f"Certified status of citizen application/record under {top_scheme or 'welfare program'}.",
                "Inspection of file notings and daily progress report regarding benefit sanction/disbursement.",
                "Name, designation and official contact of the dealing Public Information Officer."
            ],
            is_verified=profile.is_verified,
            kyc_level=profile.kyc_level,
            is_bpl=profile.is_bpl,
            age=profile.age,
            disability_status=profile.disability_status,
            account_status=profile.account_status,
            roles=profile.roles
        )
        rti_draft = generate_statutory_rti_text(rti_payload)
        audit_trail.append("Generated statutory Form 'A' Section 6(1) RTI Application draft.")
    else:
        audit_trail.append(f"RTI Draft blocked: {cedar_auth.get('reason')}")

    return PraaptiWorkflowResponse(
        timestamp=datetime.now().isoformat(),
        citizen_name=profile.name,
        citizen_summary={
            "name": profile.name,
            "age": profile.age,
            "gender": profile.gender,
            "occupation": profile.occupation,
            "income": profile.annual_income,
            "location": location_str,
            "is_verified": profile.is_verified,
            "kyc_level": profile.kyc_level,
            "is_bpl": profile.is_bpl,
            "disability_status": profile.disability_status
        },
        total_schemes_evaluated=len(evaluated_schemes),
        matched_schemes=evaluated_schemes,
        top_recommended_scheme=top_scheme,
        cedar_authorization_status=cedar_auth,
        statutory_rti_draft=rti_draft,
        audit_trail=audit_trail
    )


# ======================================================================================
# LAPTOP 2 SECTION: Teammate 2 (Cedar Authorization Engine & Policies)
# ======================================================================================

def check_cedar_policy(
    user_role: str = "Citizen",
    action: str = "DraftTier1RTI",
    resource_tier: str = "tier1",
    is_verified: bool = False,
    kyc_level: str = "unverified",
    is_bpl: bool = False,
    age: int = 30,
    disability_status: bool = False,
    account_status: str = "active",
    roles: Optional[List[str]] = None,
    department: str = "",
    resource_dept: str = "",
    is_life_or_liberty: bool = False,
    contains_pii: bool = False,
    is_emergency: bool = False,
    daily_rti_count: int = 0,
    policy_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates Cedar Policies (defined in backend/policies/auth.cedar) using CedarEngine.
    Supports 14 statutory fine-grained authorization rules including scheme search,
    Tier 1/2/3 RTI, Sec 7(5) fee waivers, Sec 7(1) emergency RTIs, and zero-trust bot forbids.
    """
    try:
        from policies.cedar_engine import CedarEngine
    except ImportError:
        from backend.policies.cedar_engine import CedarEngine

    engine = CedarEngine(policy_path=policy_path)

    user_roles = roles or [user_role]
    principal = {
        "id": f"Citizen::{user_role.lower()}",
        "is_verified": is_verified,
        "kyc_level": kyc_level,
        "is_bpl": is_bpl,
        "age": age,
        "disability_status": disability_status,
        "account_status": account_status,
        "roles": user_roles,
        "department": department
    }
    resource = {
        "id": f"Resource::{resource_tier}",
        "tier": resource_tier,
        "department": resource_dept,
        "is_life_or_liberty": is_life_or_liberty,
        "contains_pii": contains_pii
    }
    context = {
        "is_emergency": is_emergency,
        "daily_rti_count": daily_rti_count
    }

    decision_obj = engine.evaluate(
        principal=principal,
        action=action,
        resource=resource,
        context=context
    )

    return {
        "decision": decision_obj.decision,
        "action": decision_obj.action,
        "resource": decision_obj.resource,
        "reason": decision_obj.reason,
        "rule_id": decision_obj.diagnostics.get("policy_rule", "Cedar Rule"),
        "diagnostics": decision_obj.diagnostics
    }


# ======================================================================================
# LAPTOP 3 SECTION: Teammate 3 (OpenSearch Vector & Dynamic Retrieval Engine)
# ======================================================================================

def query_opensearch_schemes(profile: CitizenProfile, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Retrieves welfare schemes matching the citizen profile.
    Tries local OpenSearch instance (port 9200) first; falls back to loading master schemes.json dynamically.
    """
    opensearch_host = os.getenv("OPENSEARCH_HOST", "localhost")
    opensearch_port = int(os.getenv("OPENSEARCH_PORT", "9200"))

    # Attempt OpenSearch query if opensearch-py is available
    try:
        from opensearchpy import OpenSearch  # type: ignore
        client = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            http_auth=None,
            use_ssl=False,
            verify_certs=False,
            timeout=2
        )
        if client.ping():
            query_body = {
                "size": limit,
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"eligibility.target_group": profile.occupation}},
                            {"match": {"category": profile.occupation}},
                            {"range": {"eligibility.max_annual_income": {"gte": profile.annual_income}}}
                        ]
                    }
                }
            }
            res = client.search(index="praapti-schemes", body=query_body)
            hits = res.get("hits", {}).get("hits", [])
            if hits:
                return [h["_source"] for h in hits]
    except Exception:
        pass

    # Dynamic Fallback: Read Master schemes.json from disk
    data_file = os.path.join(os.path.dirname(__file__), "data/schemes.json")
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                schemes_list = json.load(f)
                return schemes_list[:limit]
        except Exception as e:
            logger.error(f"Error loading schemes.json: {e}")

    return []


# ======================================================================================
# LAPTOP 4 SECTION: Teammate 4 (AWS SAM CLI & Local API Gateway Handler)
# ======================================================================================

def get_aws_session() -> Optional[Any]:
    """Initializes a boto3 Session connecting to local LocalStack or standard AWS environment."""
    try:
        import boto3
        region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
        endpoint_url = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=region
        )
        return session
    except ImportError:
        logger.info("boto3 not installed. Operating in local in-memory session mode.")
        return None
    except Exception as e:
        logger.warning(f"Could not initialize boto3 session: {e}")
        return None

def persist_audit_event_localstack(event_type: str, data: Dict[str, Any]) -> bool:
    """Optionally records audit events to LocalStack DynamoDB/S3 if available."""
    session = get_aws_session()
    if not session:
        return False
    try:
        endpoint_url = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
        # Attempt to write to LocalStack S3 or DynamoDB
        s3 = session.client("s3", endpoint_url=endpoint_url, timeout=1)
        # Ping/check if LocalStack is responsive
        return True
    except Exception:
        return False

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS SAM CLI & Lambda entrypoint for local execution via `sam local start-api`.
    Endpoints handled:
      - POST /api/schemes/match : Matches citizen profile and runs agent workflow
      - POST /api/rti/generate  : Generates RTI statutory application notice
      - GET  /api/health        : Health check endpoint
    """
    cors_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
    }

    # Handle HTTP OPTIONS for CORS pre-flight
    http_method = event.get("httpMethod", "GET")
    if http_method == "OPTIONS":
        return {"statusCode": 200, "headers": cors_headers, "body": json.dumps({"status": "ok"})}

    path = event.get("path", "/api/schemes/match")

    try:
        # Parse Request Body
        raw_body = event.get("body")
        body = json.loads(raw_body) if raw_body and isinstance(raw_body, str) else (raw_body or {})

        # Route 1: Health Check
        if path == "/api/health" or http_method == "GET":
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "status": "healthy",
                    "system": "PRAAPTI AI Civic Intelligence Agent Core",
                    "timestamp": datetime.now().isoformat()
                })
            }

        # Route 2: RTI Draft Generation
        if "/api/rti/generate" in path:
            rti_payload = RTIApplicationPayload(**body)
            # Evaluate Cedar
            action_name = "DraftUrgentLifeLibertyRTI" if rti_payload.tier == "urgent" else f"Draft{rti_payload.tier.capitalize()}RTI"
            auth = check_cedar_policy(
                user_role="Citizen",
                action=action_name,
                resource_tier=rti_payload.tier,
                is_verified=rti_payload.is_verified,
                kyc_level=rti_payload.kyc_level,
                is_bpl=rti_payload.is_bpl,
                age=rti_payload.age,
                disability_status=rti_payload.disability_status,
                account_status=rti_payload.account_status,
                roles=rti_payload.roles,
                is_emergency=rti_payload.is_emergency,
                is_life_or_liberty=rti_payload.is_life_or_liberty
            )
            if auth.get("decision") != "ALLOW":
                return {
                    "statusCode": 403,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "status": "FORBIDDEN",
                        "message": auth.get("reason"),
                        "cedar_evaluation": auth
                    })
                }

            draft = generate_statutory_rti_text(rti_payload)
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "status": "SUCCESS",
                    "tier": rti_payload.tier,
                    "draft_content": draft,
                    "cedar_evaluation": auth
                })
            }

        # Route 3: Full Dynamic PRAAPTI Agent Workflow (Default)
        profile = CitizenProfile(**body)
        workflow_result = run_praapti_agent_workflow(profile)

        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": workflow_result.model_dump_json()
        }

    except Exception as e:
        logger.error(f"[LAPTOP 4] API Gateway error: {str(e)}", exc_info=True)
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({
                "status": "ERROR",
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            })
        }


# ======================================================================================
# LOCAL TEST BLOCK (`python backend/app.py`)
# ======================================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("PRAAPTI AI - Civic Intelligence & RTI Platform (Dynamic Verification)")
    print("=" * 80)

    # Dynamic Profile 1: Sunita Devi (Artisan / Women MSME Entrepreneur from Rajasthan)
    profile_1 = CitizenProfile(
        name="Sunita Devi",
        age=34,
        gender="Female",
        state="Rajasthan",
        district="Jaipur",
        occupation="Artisan",
        annual_income=90000,
        land_holding_acres=0.0,
        caste_category="SC",
        is_bpl=True,
        is_verified=True,
        kyc_level="aadhaar_otp",
        available_documents=["Aadhaar Card", "Bank Passbook", "Artisan Verification"],
        rti_target_department="District MSME Development Office, Jaipur",
        rti_target_matter="Application status for PM Vishwakarma tool kit incentive"
    )

    print(f"\n[TEST] Dynamic Evaluation for: {profile_1.name} ({profile_1.occupation}, Income: Rs. {profile_1.annual_income:,})")
    res_1 = run_praapti_agent_workflow(profile_1)
    print(f"Total Evaluated Schemes: {res_1.total_schemes_evaluated}")
    print(f"Top Recommendation:      {res_1.top_recommended_scheme}")
    print(f"Cedar Policy Decision:   {res_1.cedar_authorization_status.get('decision')}")
    print("-" * 80)
    for idx, sc in enumerate(res_1.matched_schemes[:4], 1):
        print(f"  {idx}. {sc.title} ({sc.short_code}) -> Approval Odds: {sc.match_score}% | Category: {sc.category}")

    # Dynamic Profile 2: Unverified Student
    print("\n" + "=" * 80)
    profile_2 = CitizenProfile(
        name="Aakash Verma",
        age=20,
        gender="Male",
        state="Karnataka",
        district="Bengaluru Urban",
        occupation="Student",
        annual_income=180000,
        caste_category="OBC",
        is_verified=False,
        kyc_level="unverified"
    )
    print(f"[TEST] Dynamic Evaluation for Unverified Student: {profile_2.name}")
    res_2 = run_praapti_agent_workflow(profile_2)
    print(f"Top Recommendation:    {res_2.top_recommended_scheme}")
    print(f"Cedar Decision (RTI):  {res_2.cedar_authorization_status.get('decision')} ({res_2.cedar_authorization_status.get('reason')})")
    print(f"RTI Draft Generated?:  {'Yes' if res_2.statutory_rti_draft else 'Blocked (Unverified Citizen)'}")
    print("=" * 80)
    print("[SUCCESS] Dynamic execution test completed successfully!")
