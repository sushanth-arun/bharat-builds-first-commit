// ==============================================================================
// PRAAPTI AI - Cedar Authorization Policies (auth.cedar)
// Indian Welfare Scheme Discovery & Statutory RTI Drafting Access Control
// ==============================================================================

// Rule 1: Allow all citizens (verified or unverified) to search and discover public welfare schemes
permit (
    principal,
    action in [Action::"SearchSchemes", Action::"ViewSchemeDetails", Action::"CheckEligibility"],
    resource
);

// Rule 2: Permit verified citizens to generate Tier 1 RTI (PIO Initial Application) and Tier 2 RTI (First Appellate Authority)
permit (
    principal,
    action in [Action::"DraftTier1RTI", Action::"DraftTier2RTI"],
    resource
)
when {
    principal.is_verified == true
};

// Rule 3: Permit verified citizens with high-trust KYC (e.g. Aadhaar / DigiLocker linked) to draft Tier 3 CIC (Central Information Commission) Appeals
permit (
    principal,
    action == Action::"DraftTier3CICAppeal",
    resource
)
when {
    principal.is_verified == true &&
    principal.kyc_level in ["aadhaar_otp", "digilocker", "offline_kyc"]
};

// Rule 4: FORBID unverified accounts from generating Tier 3 CIC Second Appeals (Statutory Safeguard against malicious bot appeals)
forbid (
    principal,
    action == Action::"DraftTier3CICAppeal",
    resource
)
when {
    principal.is_verified == false
};

// Rule 5: Permit RTI officers and system auditors to inspect generated RTI drafting history
permit (
    principal in Role::"Auditor",
    action in [Action::"AuditRTIHistory", Action::"ExportRTIArchive"],
    resource
);
