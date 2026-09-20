# PRAAPTI AI (प्राप्ति AI)
> **P**radhanmantri & **R**ajya **A**ssistance **A**pplication, **P**robability, and **T**ransparency **I**nterface  
> *Civic Intelligence Platform for Indian Welfare Schemes & Statutory RTI Drafting*

Built for **Track 1 ("Build It")** of the **WeMakeDevs AWS Hackathon**. Runs **100% locally** on open-source tools without requiring an AWS Cloud Account.

---

## 🏗️ Architecture & Component Mapping
 
| Subsystem | Technology | Teammate Role |
| :--- | :--- | :--- |
| **Agent Core & Dynamic Orchestration** | Strands Agents SDK & Custom `@tool` Workflows | **Teammate 1 (Sushanth)** |
| **Civic Dashboard, Real-Time AI UI & Workflows** | Accessible Responsive UI, Live Chat & Results Portal | **Teammate 2 (Sanjay)** |
| **Zero-Trust Authorization & Policy Engine** | AWS Cedar Engine (`auth.cedar` & `cedar_engine.py`) | **Teammate 3 (Ratheeswar)** |
| **Dynamic Welfare Knowledgebase & Vector Search** | OpenSearch Indexing & Scheme Retrieval (`scheme_indexer.py`) | **Teammate 4 (Harsh)** |

---

## 📂 Project Structure

```text
praapti-ai/
├── backend/
│   ├── app.py                     # Main Strands Agent Entrypoint, Custom @tools & Workflows
│   ├── templates/
│   │   ├── index.html             # Citizen Intake Form & Dashboard
│   │   ├── results.html           # Scheme Evaluations & Real-time AI Assistant
│   │   └── serve_ui.py            # Local HTTP & Agent API Web Server (Port 8080)
│   ├── policies/
│   │   ├── auth.cedar             # Cedar Authorization Rules (Tier 1/2/3 RTI)
│   │   └── cedar_engine.py        # Local Cedar Evaluation Wrapper
│   ├── search/
│   │   └── scheme_indexer.py      # OpenSearch Ingestion & Query Client
│   └── data/
│       ├── schemes.json           # Master DB (Central & State Welfare Schemes)
│       └── districts.json         # 700+ Mapped Indian Districts
├── .env.example                   # Local environment variable blueprint
└── README.md
```

---

## 🚀 Quickstart (100% Local Development)

### 1. Configure Python Environment
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run PRAAPTI AI Dashboard & Civic Intelligence Server
```bash
python backend/templates/serve_ui.py
```
Open `http://localhost:8080` in your web browser.

### 3. Test Cedar Policy Authorization Engine
```bash
python backend/policies/cedar_engine.py
```

### 4. Run Strands Agent Core in CLI
```bash
python backend/app.py
```

---

## 📜 Statutory Cedar Policies

`backend/policies/auth.cedar` implements 14 fine-grained zero-trust statutory rules for civic transactions under the RTI Act, 2005:

- **Category 1: Public Discovery & Anti-Scam**
  - **Rule 1**: Open access to search, view details, check eligibility, and export welfare scheme guides (`SearchSchemes`, `ViewSchemeDetails`, `CheckEligibility`, `ExportSchemeGuide`).
  - **Rule 2**: Open permission to flag fraudulent portals or report phishing domains (`FlagSuspiciousScheme`, `ReportPhishingDomain`).

- **Category 2: Statutory RTI Drafting & Fee Exemptions (RTI Act 2005)**
  - **Rule 3**: Verified citizens with active accounts are permitted to draft Tier 1 (PIO Sec 6(1)) and Tier 2 (FAA Sec 19(1)) RTIs.
  - **Rule 4**: Tier 3 CIC/SIC Second Appeals (Sec 19(3)) require verified high-trust KYC (`aadhaar_otp`, `digilocker`, `offline_kyc`).
  - **Rule 5**: Statutory fee waiver (`ClaimRTIFeeExemption` under Sec 7(5)) for Below Poverty Line (BPL) cardholders, Senior Citizens (60+ yrs), or Divyangjan (PwD).
  - **Rule 6**: Expedited 48-Hour Emergency Life or Liberty RTI drafting (`DraftUrgentLifeLibertyRTI` under Sec 7(1) Proviso).

- **Category 3: Anti-Bot & Zero-Trust Forbid Rules**
  - **Rule 7 (Forbid)**: Suspended, blacklisted, or bot-flagged accounts are strictly forbidden from filing legal RTIs or claiming fee waivers.
  - **Rule 8 (Forbid)**: Unverified accounts are strictly forbidden from filing Tier 3 CIC Second Appeals (bot spam prevention).
  - **Rule 9 (Forbid)**: Unverified accounts are forbidden from using the expedited 48-Hour Emergency RTI route.
  - **Rule 10 (Forbid)**: Daily submission volume limit (10 RTIs/day rate limit) strictly enforced for non-superusers.

- **Category 4: Governance, Audit & PII Protection**
  - **Rule 11**: Certified Auditors permitted to inspect RTI logs and export compliance archives (`AuditRTIHistory`, `InspectAnonymizedLogs`, `ExportRTIArchive`).
  - **Rule 12**: PIO Officers permitted to inspect citizen grievances for their assigned department (`InspectCitizenGrievance`, `VerifyApplicantKYC`, `UpdateRTIStatus`).
  - **Rule 13**: System Administrators granted full administrative governance access.
  - **Rule 14 (Forbid)**: Data Privacy Safeguard strictly forbids unredacted citizen PII export for non-admin/non-auditor roles.
