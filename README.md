# PRAAPTI AI (प्राप्ति AI)
> **P**radhanmantri & **R**ajya **A**ssistance **A**pplication, **P**robability, and **T**ransparency **I**nterface  
> *Civic Intelligence Platform for Indian Welfare Schemes & Statutory RTI Drafting*

Built for **Track 1 ("Build It")** of the **WeMakeDevs AWS Hackathon**. Runs **100% locally** on open-source tools without requiring an AWS Cloud Account.

---

## 🏗️ Architecture & Component Mapping
 
| Subsystem | Technology | Teammate Role |
| :--- | :--- | :--- |
| **Agent Core & Orchestration** | Strands Agents SDK (Python) | Teammate 1 |
| **Modern Civic Dashboard & Chatbot** | Accessible Vanilla Responsive UI & Agent Tools | Teammate 1 |
| **Authorization & Policy Engine** | Cedar Zero-Trust Policy Engine (`auth.cedar`) | Teammate 2 |
| **Knowledge Base & Vector Search** | OpenSearch & Dynamic Scheme Knowledgebase | Teammate 3 |
| **Unified Local API Dispatcher** | Pure Python & JSON API Server | Teammate 4 |

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

`backend/policies/auth.cedar` implements fine-grained zero-trust rules for civic transactions:
- **Rule 1**: All citizens can search public welfare schemes (`SearchSchemes`).
- **Rule 2**: Verified citizens are permitted to draft **Tier 1 (PIO)** and **Tier 2 (FAA)** RTIs.
- **Rule 3 & 4**: **Tier 3 (CIC Second Appeal)** explicitly **FORBIDS** unverified accounts and requires verified KYC (`aadhaar_otp` or `digilocker`).
