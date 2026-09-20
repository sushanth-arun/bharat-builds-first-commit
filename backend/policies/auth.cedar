// ==============================================================================
// PRAAPTI AI (प्राप्ति AI) - Advanced Cedar Authorization Ruleset (auth.cedar)
// Zero-Trust Statutory Governance, RTI Act 2005 Access Control & Anti-Bot Engine
// ==============================================================================

// ------------------------------------------------------------------------------
// CATEGORY 1: PUBLIC CIVIC DISCOVERY & ANTI-SCAM TRANSPARENCY
// ------------------------------------------------------------------------------

// Rule 1: Public Welfare Scheme Discovery & Eligibility Assessment
// Allows all citizens (verified or unverified) to search, view, and check eligibility for public schemes.
permit (
    principal,
    action in [
        Action::"SearchSchemes",
        Action::"ViewSchemeDetails",
        Action::"CheckEligibility",
        Action::"ExportSchemeGuide"
    ],
    resource
);

// Rule 2: Anti-Scam Phishing & Fraud Reporting
// Permits any citizen to report fraudulent portals, scam messages, or phishing domains.
permit (
    principal,
    action in [
        Action::"FlagSuspiciousScheme",
        Action::"ReportPhishingDomain"
    ],
    resource
);

// ------------------------------------------------------------------------------
// CATEGORY 2: STATUTORY RTI DRAFTING & FEE EXEMPTIONS (RTI ACT, 2005)
// ------------------------------------------------------------------------------

// Rule 3: Tier 1 PIO (Sec 6(1)) and Tier 2 FAA (Sec 19(1)) RTI Application Drafting
// Permits verified citizens with active account status to draft Tier 1 and Tier 2 RTIs.
permit (
    principal,
    action in [
        Action::"DraftTier1RTI",
        Action::"DraftTier2RTI"
    ],
    resource
)
when {
    principal.is_verified == true &&
    principal.account_status == "active"
};

// Rule 4: Tier 3 CIC / SIC Second Appeal Drafting (Sec 19(3))
// Requires high-trust verified KYC (Aadhaar OTP, DigiLocker, or Offline KYC) to prevent bot spamming of Information Commissions.
permit (
    principal,
    action == Action::"DraftTier3CICAppeal",
    resource
)
when {
    principal.is_verified == true &&
    principal.account_status == "active" &&
    principal.kyc_level in ["aadhaar_otp", "digilocker", "offline_kyc"]
};

// Rule 5: Statutory RTI Fee Exemption & Waiver Claims (Sec 7(5))
// Grants statutory RTI application fee waiver for Below Poverty Line (BPL) citizens, Senior Citizens (60+), or Divyangjan (PwD).
permit (
    principal,
    action == Action::"ClaimRTIFeeExemption",
    resource
)
when {
    principal.is_verified == true &&
    (
        principal.is_bpl == true ||
        principal.age >= 60 ||
        principal.disability_status == true
    )
};

// Rule 6: Emergency Life or Liberty 48-Hour RTI Expedited Drafting (Sec 7(1) Proviso)
// Permits expedited 48-hour turnaround RTI drafting for urgent matters concerning life or liberty.
permit (
    principal,
    action == Action::"DraftUrgentLifeLibertyRTI",
    resource
)
when {
    principal.is_verified == true &&
    principal.account_status == "active" &&
    (
        context.is_emergency == true ||
        resource.is_life_or_liberty == true
    )
};

// ------------------------------------------------------------------------------
// CATEGORY 3: BOT SAFEGUARDS, SECURITY & FORBID RULES (OVERRIDE PERMITS)
// ------------------------------------------------------------------------------

// Rule 7: FORBID Suspended or Flagged Accounts from Filing Statutory RTIs
// Suspended or blacklisted accounts are strictly forbidden from generating legal RTI notices.
forbid (
    principal,
    action in [
        Action::"DraftTier1RTI",
        Action::"DraftTier2RTI",
        Action::"DraftTier3CICAppeal",
        Action::"DraftUrgentLifeLibertyRTI",
        Action::"ClaimRTIFeeExemption"
    ],
    resource
)
when {
    principal.account_status in ["suspended", "blacklisted", "flagged_bot"]
};

// Rule 8: FORBID Unverified Accounts from Tier 3 Second Appeals
// Prevents automated bots and unverified users from spamming Central/State Information Commissions.
forbid (
    principal,
    action == Action::"DraftTier3CICAppeal",
    resource
)
when {
    principal.is_verified == false
};

// Rule 9: FORBID Abuse of 48-Hour Emergency Life or Liberty Route by Unverified Users
forbid (
    principal,
    action == Action::"DraftUrgentLifeLibertyRTI",
    resource
)
when {
    principal.is_verified == false ||
    principal.kyc_level == "unverified"
};

// Rule 10: FORBID Daily Bulk Submission Limit Exceeded (Anti-Spam Rate Limit)
forbid (
    principal,
    action in [
        Action::"DraftTier1RTI",
        Action::"DraftTier2RTI",
        Action::"DraftTier3CICAppeal",
        Action::"DraftUrgentLifeLibertyRTI"
    ],
    resource
)
when {
    context.daily_rti_count >= 10
}
unless {
    principal in Role::"SuperUser"
};

// ------------------------------------------------------------------------------
// CATEGORY 4: GOVERNANCE, AUDIT, PIO INTAKE & COMPLIANCE
// ------------------------------------------------------------------------------

// Rule 11: System Auditor RTI Audit & Compliance Access
// Grants certified Auditors permissions to inspect RTI drafting history and export compliance archives.
permit (
    principal in Role::"Auditor",
    action in [
        Action::"AuditRTIHistory",
        Action::"InspectAnonymizedLogs",
        Action::"ExportRTIArchive"
    ],
    resource
);

// Rule 12: Public Information Officer (PIO) Official Grievance Intake
// Permits PIO Officers to inspect citizen RTI applications for their designated department.
permit (
    principal in Role::"PIO_Officer",
    action in [
        Action::"InspectCitizenGrievance",
        Action::"VerifyApplicantKYC",
        Action::"UpdateRTIStatus"
    ],
    resource
)
when {
    resource.department == principal.department
};

// Rule 13: System Administrator Full Administrative Access
permit (
    principal in Role::"SystemAdmin",
    action,
    resource
);

// Rule 14: Data Privacy Safeguard - FORBID Unredacted Citizen PII Export for Non-Admins
forbid (
    principal,
    action in [
        Action::"ExportRawCitizenPII",
        Action::"ViewUnredactedAadhaar"
    ],
    resource
)
when {
    resource.contains_pii == true
}
unless {
    principal in Role::"SystemAdmin" ||
    principal in Role::"Auditor"
};

