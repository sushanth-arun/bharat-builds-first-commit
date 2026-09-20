import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def create_element(name):
    return OxmlElement(name)

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_heading_styled(doc, text, level):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    for run in p.runs:
        run.font.name = 'Calibri'
        if level == 1:
            run.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D) # Deep Navy
            run.font.size = Pt(18)
            run.bold = True
        elif level == 2:
            run.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C) # Ocean Blue
            run.font.size = Pt(14)
            run.bold = True
        elif level == 3:
            run.font.color.rgb = RGBColor(0x33, 0x33, 0x33) # Charcoal
            run.font.size = Pt(12)
            run.bold = True
    return p

def add_code_block(doc, code_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.left_indent = Inches(0.2)
    
    # We can use a single-cell table for shaded code block
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F6F8")
    set_cell_margins(cell, top=120, bottom=120, left=180, right=180)
    
    cp = cell.paragraphs[0]
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(2)
    run = cp.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def build_document():
    doc = docx.Document()
    
    # Page setup - 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title Banner
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title_p.add_run("PRAAPTI AI (प्राप्ति AI)")
    run_title.font.name = 'Calibri'
    run_title.font.size = Pt(24)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(18)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = sub_p.add_run("Advanced Statutory Cedar Policy Architecture & Change Documentation\nCivic Intelligence & RTI Act 2005 Access Control System")
    run_sub.font.name = 'Calibri'
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Section 1: Executive Summary
    add_heading_styled(doc, "1. Executive Summary", level=1)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.add_run("This document provides a comprehensive technical overview of the advanced ")
    r_bold = p.add_run("Cedar Authorization Policy Engine")
    r_bold.bold = True
    p.add_run(" implemented for ")
    r_app = p.add_run("PRAAPTI AI (प्राप्ति AI)")
    r_app.bold = True
    p.add_run(" — Pradhanmantri & Rajya Assistance Application, Probability, and Transparency Interface.\n\n"
          "The project context requires strict statutory governance under the ")
    r_rti = p.add_run("Right to Information (RTI) Act, 2005")
    r_rti.bold = True
    p.add_run(", balancing open public welfare scheme discovery with fine-grained zero-trust protection against bot spamming, identity forgery, rate limit abuse, and unauthorized citizen PII extraction.")

    # Section 2: Key Architecture & Statutory Categories
    add_heading_styled(doc, "2. Key Policy Categories & Statutory Mapping", level=1)
    
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.add_run("The upgraded policy framework replaces simple single-rule permissions with ")
    p.add_run("14 fine-grained statutory rules").bold = True
    p.add_run(" organized across four operational categories:")

    # Category Bullet 1
    p1 = doc.add_paragraph(style='List Bullet')
    p1.paragraph_format.space_after = Pt(4)
    r = p1.add_run("Category 1: Public Civic Discovery & Anti-Scam Transparency\n")
    r.bold = True
    r.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    p1.add_run("Provides open access for all citizens (verified or unverified) to search schemes, check eligibility, export guides, and report fraudulent portals or phishing URLs.")

    # Category Bullet 2
    p2 = doc.add_paragraph(style='List Bullet')
    p2.paragraph_format.space_after = Pt(4)
    r = p2.add_run("Category 2: Statutory RTI Drafting & Fee Exemptions (RTI Act 2005)\n")
    r.bold = True
    r.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    p2.add_run("Governs drafting rights for Tier 1 PIO (Sec 6(1)), Tier 2 FAA Appeals (Sec 19(1)), Tier 3 CIC Appeals (Sec 19(3)), statutory fee waivers for BPL/Senior Citizens/PwD (Sec 7(5)), and 48-Hour Emergency Life/Liberty RTIs (Sec 7(1) Proviso).")

    # Category Bullet 3
    p3 = doc.add_paragraph(style='List Bullet')
    p3.paragraph_format.space_after = Pt(4)
    r = p3.add_run("Category 3: Bot Safeguards, Rate Limiting & Zero-Trust Forbid Rules\n")
    r.bold = True
    r.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    p3.add_run("Uses Cedar's explicit 'forbid' statement (which strictly overrides 'permit') to block suspended/blacklisted accounts, unverified Tier 3 CIC spamming, unverified emergency route abuse, and daily volume threshold breaches (>10 RTIs/day).")

    # Category Bullet 4
    p4 = doc.add_paragraph(style='List Bullet')
    p4.paragraph_format.space_after = Pt(8)
    r = p4.add_run("Category 4: Governance, Audit, PIO Intake & Data Privacy Safeguards\n")
    r.bold = True
    r.font.color.rgb = RGBColor(0x00, 0x5A, 0x9C)
    p4.add_run("Grants certified Auditors compliance inspection rights, restricts PIO Officer access to their assigned department, and enforces Data Privacy Safeguards against unredacted PII export.")

    # Section 3: Summary Table of 14 Cedar Policy Rules
    add_heading_styled(doc, "3. Summary of 14 Cedar Authorization Rules", level=1)
    
    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Table Header
    hdr_cells = table.rows[0].cells
    hdr_titles = ["Rule #", "Type", "Action / Target", "Statutory Basis / Condition", "Decision Logic"]
    col_widths = [Inches(0.7), Inches(0.8), Inches(1.8), Inches(1.8), Inches(1.4)]
    
    for i, title in enumerate(hdr_titles):
        cell = hdr_cells[i]
        cell.width = col_widths[i]
        set_cell_background(cell, "1B365D")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    rules_data = [
        ("Rule 1", "permit", "SearchSchemes, ViewSchemeDetails, CheckEligibility", "Public civic open access", "ALLOW for all citizens"),
        ("Rule 2", "permit", "FlagSuspiciousScheme, ReportPhishingDomain", "Anti-scam civic defense", "ALLOW for all citizens"),
        ("Rule 3", "permit", "DraftTier1RTI, DraftTier2RTI", "RTI Act Sec 6(1) & Sec 19(1)", "ALLOW if verified & active"),
        ("Rule 4", "permit", "DraftTier3CICAppeal", "RTI Act Sec 19(3) Second Appeal", "ALLOW if Aadhaar/DigiLocker KYC"),
        ("Rule 5", "permit", "ClaimRTIFeeExemption", "RTI Act Sec 7(5) Fee Waiver", "ALLOW if BPL, 60+ yrs, or PwD"),
        ("Rule 6", "permit", "DraftUrgentLifeLibertyRTI", "RTI Act Sec 7(1) 48-Hr Proviso", "ALLOW if verified & emergency"),
        ("Rule 7", "forbid", "Draft RTI / Fee Waiver", "Account status in [suspended, blacklisted]", "DENY (Overrides Permit)"),
        ("Rule 8", "forbid", "DraftTier3CICAppeal", "Unverified account bot safeguard", "DENY (Overrides Permit)"),
        ("Rule 9", "forbid", "DraftUrgentLifeLibertyRTI", "Unverified emergency route abuse", "DENY (Overrides Permit)"),
        ("Rule 10", "forbid", "Draft Tier 1/2/3/Urgent RTI", "Daily limit exceeded (>=10 RTIs)", "DENY unless SuperUser"),
        ("Rule 11", "permit", "AuditRTIHistory, ExportRTIArchive", "Compliance & Audit governance", "ALLOW for Role::Auditor"),
        ("Rule 12", "permit", "InspectCitizenGrievance, VerifyKYC", "PIO Departmental jurisdiction", "ALLOW if dept matches"),
        ("Rule 13", "permit", "All Actions", "System Administrator role", "ALLOW for Role::SystemAdmin"),
        ("Rule 14", "forbid", "ExportRawCitizenPII, ViewUnredactedAadhaar", "Data Privacy & PII protection", "DENY unless Admin/Auditor")
    ]

    for rule in rules_data:
        row_cells = table.add_row().cells
        for i, val in enumerate(rule):
            cell = row_cells[i]
            cell.width = col_widths[i]
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            
            # Shading for Forbid rules vs Permit
            if rule[1] == "forbid":
                set_cell_background(cell, "FFF0F0") # Light Red tint
            else:
                set_cell_background(cell, "F9FAFC")

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            run = p.add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(9)
            if i == 0:
                run.bold = True
            elif i == 1:
                run.bold = True
                run.font.color.rgb = RGBColor(0xB2, 0x22, 0x22) if val == "forbid" else RGBColor(0x00, 0x64, 0x00)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Section 4: Detailed Breakdown of File Changes
    add_heading_styled(doc, "4. Detailed Breakdown of Codebase Changes", level=1)

    # File 1
    add_heading_styled(doc, "4.1 backend/policies/auth.cedar", level=2)
    p = doc.add_paragraph()
    p.add_run("Updated the core Cedar policy definitions to include complete 14-rule zero-trust ruleset with Cedar 'when' and 'unless' condition blocks.")
    add_code_block(doc, 
"// Rule 4: Tier 3 CIC / SIC Second Appeal Drafting (Sec 19(3))\n"
"permit (\n"
"    principal,\n"
"    action == Action::\"DraftTier3CICAppeal\",\n"
"    resource\n"
")\n"
"when {\n"
"    principal.is_verified == true &&\n"
"    principal.account_status == \"active\" &&\n"
"    principal.kyc_level in [\"aadhaar_otp\", \"digilocker\", \"offline_kyc\"]\n"
"};\n\n"
"// Rule 7: FORBID Suspended or Flagged Accounts from Filing Statutory RTIs\n"
"forbid (\n"
"    principal,\n"
"    action in [\n"
"        Action::\"DraftTier1RTI\", Action::\"DraftTier2RTI\",\n"
"        Action::\"DraftTier3CICAppeal\", Action::\"DraftUrgentLifeLibertyRTI\"\n"
"    ],\n"
"    resource\n"
")\n"
"when {\n"
"    principal.account_status in [\"suspended\", \"blacklisted\", \"flagged_bot\"]\n"
"};"
    )

    # File 2
    add_heading_styled(doc, "4.2 backend/policies/cedar_engine.py", level=2)
    p = doc.add_paragraph()
    p.add_run("Refactored ")
    p.add_run("CedarEngine").bold = True
    p.add_run(" class to support both native ")
    p.add_run("cedarpy").bold = True
    p.add_run(" binding entity-parsing and a high-precision local Python evaluation fallback. Implemented explicit 3-phase evaluation order: ")
    p.add_run("Phase 1: Forbid Rules -> Phase 2: Permit Rules -> Phase 3: Default Deny").bold = True
    p.add_run(".\nIncluded an automated ")
    p.add_run("8-scenario self-test suite").bold = True
    p.add_run(" verifying every statutory edge case.")

    # File 3
    add_heading_styled(doc, "4.3 backend/app.py", level=2)
    p = doc.add_paragraph()
    p.add_run("Extended ")
    p.add_run("CitizenProfile").bold = True
    p.add_run(" and ")
    p.add_run("RTIApplicationPayload").bold = True
    p.add_run(" Pydantic v2 schemas with advanced statutory fields: ")
    p.add_run("is_bpl, age, disability_status, account_status, roles, is_emergency, is_life_or_liberty, claim_fee_waiver").italic = True
    p.add_run(".\nUpdated ")
    p.add_run("check_cedar_policy()").bold = True
    p.add_run(" and ")
    p.add_run("run_praapti_agent_workflow()").bold = True
    p.add_run(" to pass all attributes dynamically into ")
    p.add_run("CedarEngine").bold = True
    p.add_run(".")

    # File 4 & 5
    add_heading_styled(doc, "4.4 backend/templates/serve_ui.py & README.md", level=2)
    p = doc.add_paragraph()
    p.add_run("Updated local HTTP server endpoints (")
    p.add_run("/api/rti/generate").bold = True
    p.add_run(" and ")
    p.add_run("/api/workflow").bold = True
    p.add_run(") to process extended payload attributes. Updated ")
    p.add_run("README.md").bold = True
    p.add_run(" documenting all 14 statutory Cedar rules.")

    # Section 5: Empirical Verification & Test Results
    add_heading_styled(doc, "5. Empirical Verification & Test Results", level=1)
    p = doc.add_paragraph()
    p.add_run("All changes were validated through execution of unit test suites and integration tests. Summary of execution output:")

    table_tests = doc.add_table(rows=1, cols=5)
    table_tests.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    t_hdr = table_tests.rows[0].cells
    t_titles = ["Test Scenario", "Action Tested", "Principal State", "Decision", "Rule Evaluated"]
    t_widths = [Inches(1.8), Inches(1.5), Inches(1.5), Inches(0.8), Inches(1.1)]

    for i, title in enumerate(t_titles):
        cell = t_hdr[i]
        cell.width = t_widths[i]
        set_cell_background(cell, "005A9C")
        set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(title)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(9.5)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    test_rows = [
        ("1. Unverified Tier 3 CIC", "DraftTier3CICAppeal", "is_verified=False", "DENY", "Rule 8 (Forbid)"),
        ("2. Verified Tier 1 PIO", "DraftTier1RTI", "is_verified=True, active", "ALLOW", "Rule 3 (Permit)"),
        ("3. BPL Fee Exemption", "ClaimRTIFeeExemption", "is_bpl=True", "ALLOW", "Rule 5 (Sec 7(5))"),
        ("4. Senior Citizen Waiver", "ClaimRTIFeeExemption", "age=65", "ALLOW", "Rule 5 (Sec 7(5))"),
        ("5. Suspended Account", "DraftTier1RTI", "account_status='suspended'", "DENY", "Rule 7 (Forbid)"),
        ("6. Emergency 48-Hr RTI", "DraftUrgentLifeLibertyRTI", "is_verified=True, emergency", "ALLOW", "Rule 6 (Sec 7(1))"),
        ("7. Rate Limit Exceeded", "DraftTier1RTI", "daily_rti_count=12", "DENY", "Rule 10 (Forbid)"),
        ("8. Citizen PII Export", "ExportRawCitizenPII", "roles=['Citizen'], pii=True", "DENY", "Rule 14 (Forbid)")
    ]

    for tr in test_rows:
        row_cells = table_tests.add_row().cells
        for i, val in enumerate(tr):
            cell = row_cells[i]
            cell.width = t_widths[i]
            set_cell_margins(cell, top=50, bottom=50, left=60, right=60)
            set_cell_background(cell, "FAFAFA")
            
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            run = p.add_run(val)
            run.font.name = 'Calibri'
            run.font.size = Pt(8.5)
            if i == 3:
                run.bold = True
                run.font.color.rgb = RGBColor(0x00, 0x64, 0x00) if val == "ALLOW" else RGBColor(0xB2, 0x22, 0x22)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Conclusion
    add_heading_styled(doc, "6. Conclusion", level=1)
    p_end = doc.add_paragraph()
    p_end.add_run("The upgraded Cedar authorization system for ")
    p_end.add_run("PRAAPTI AI").bold = True
    p_end.add_run(" provides a production-grade, statutory-aligned security layer. It enforces zero-trust access control for Indian welfare scheme discovery and statutory RTI drafting while maintaining 100% offline local evaluation capability.")

    output_filename = "PRAAPTI_AI_Cedar_Policies_Documentation.docx"
    doc.save(output_filename)
    print(f"[SUCCESS] Document generated successfully at: {output_filename}")

if __name__ == "__main__":
    build_document()
