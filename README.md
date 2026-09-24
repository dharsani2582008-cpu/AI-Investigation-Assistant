Yes bro 👍 This README is **outdated** — it still says Phase 1 and “local AI assistant.” Since we completed up to **Phase 8** and deployed it with **Ollama Cloud + Gemma 4:31b**, replace the GitHub `README.md` with this:

# 🔍 AI Investigation Assistant

An academic prototype web application that helps investigators analyze digital evidence from **CSV, Excel, JSON, and PDF** files using NLP-based entity extraction, relationship/link analysis, AI-assisted evidence querying, pattern detection, dashboards, and report generation.

> **Academic Prototype Disclaimer:** This is a college project prototype. It is **NOT a certified forensic tool** and its output is **NOT legally admissible**. All AI-generated findings require investigator verification.

## 🌐 Live Demo

**Streamlit Cloud:**
[https://ai-investigation-assistant-kl9u3zjvapvi4dqfzcertg.streamlit.app/](https://ai-investigation-assistant-kl9u3zjvapvi4dqfzcertg.streamlit.app/)

The application is deployed on Streamlit Cloud and uses **Ollama Cloud** for AI inference.

---

## 📌 Current Status

The core prototype is implemented through **Phase 8**.

### Completed

* ✅ Project setup and Streamlit application
* ✅ Evidence upload and validation
* ✅ CSV / Excel / JSON / PDF evidence ingestion
* ✅ Evidence preprocessing and storage
* ✅ NLP-based entity extraction
* ✅ Entity management and visualization
* ✅ Relationship and link analysis
* ✅ Network graph visualization
* ✅ Evidence-grounded AI Assistant
* ✅ Ollama Cloud integration
* ✅ Gemma 4:31b cloud model
* ✅ Pattern / investigation indicators
* ✅ Investigation dashboard with real metrics
* ✅ JSON report generation
* ✅ PDF report generation
* ✅ Navigation and manual testing
* ✅ Streamlit Cloud deployment

### Planned

* ⏳ Authentication and admin roles
* ⏳ Persistent cloud database/storage
* ⏳ Additional testing and production-level improvements

---

## 🚀 Features

### 1. Evidence Ingestion

Supports:

* CSV
* Excel (`.xlsx`)
* JSON
* PDF

Uploaded evidence is processed and assigned an internal **Evidence ID** for traceability.

---

### 2. Evidence Preprocessing

The application performs preprocessing such as:

* Data cleaning
* Structured data extraction
* Text extraction from PDFs
* Record/page tracking
* Evidence metadata management

---

### 3. NLP Entity Extraction

The system identifies entities using NLP and pattern-based extraction.

Supported entity types include:

* `PERSON`
* `ORGANIZATION`
* `LOCATION`
* `DATE`
* `EMAIL`
* `PHONE`
* `URL`
* `IP_ADDRESS`
* `TRANSACTION_ID`
* `ACCOUNT`

Entity results retain their associated evidence and record/page information where available.

---

### 4. Relationship & Link Analysis

The system identifies relationships between extracted entities and represents them as a network graph.

Examples include:

```text
PERSON → HAS_EMAIL → EMAIL
PERSON → HAS_PHONE → PHONE
PERSON → LOCATED_AT → LOCATION
PERSON → ASSOCIATED_WITH_ORGANIZATION → ORGANIZATION
PERSON → HAS_ACCOUNT → ACCOUNT
ACCOUNT → INVOLVED_IN_TRANSACTION → TRANSACTION_ID
```

The relationship terminology is intentionally neutral and evidence-based.

---

### 5. 🤖 AI Investigation Assistant

The AI Assistant allows users to ask questions about the uploaded evidence.

The system uses:

**Ollama Cloud + Gemma 4:31b**

The AI receives the relevant evidence context retrieved by the application rather than unrestricted access to the entire evidence store.

The assistant is instructed to:

* Use only supplied evidence
* Avoid inventing facts
* Reference Evidence IDs where available
* Mention record/page information
* Distinguish evidence from interpretation
* Identify conflicting evidence
* State when available evidence is insufficient
* Avoid declaring guilt or innocence

---

### 6. 📊 Investigation Dashboard

The dashboard provides an overview of:

* Evidence files
* Extracted entities
* Relationships
* Entity distribution
* Relationship distribution
* Detected descriptive indicators
* Evidence sources

Indicators are descriptive and require investigator review. They do not determine guilt or wrongdoing.

---

### 7. 📄 Report Generation

The application can generate investigation summaries in:

* JSON
* PDF

Reports include stored evidence information, extracted entities, relationships, and descriptive indicators.

---

## 🛠️ Technology Stack

| Component            | Technology                        |
| -------------------- | --------------------------------- |
| Frontend / UI        | Streamlit                         |
| Programming Language | Python                            |
| Data Processing      | Pandas                            |
| Excel Processing     | OpenPyXL                          |
| PDF Processing       | PyMuPDF                           |
| NLP                  | spaCy + Regex                     |
| Graph Analysis       | NetworkX                          |
| Visualization        | Plotly                            |
| AI Model             | Gemma 4:31b                       |
| AI Platform          | Ollama Cloud                      |
| Reports              | ReportLab                         |
| Current Storage      | JSON-based evidence/index storage |
| Deployment           | Streamlit Cloud                   |
| Version Control      | Git + GitHub                      |

---

## 📁 Project Structure

```text
AI-Investigation-Assistant/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   ├── uploads/
│   ├── processed/
│   └── sample/
│
├── models/
│   └── schemas.py
│
├── services/
│   ├── ai_assistant.py
│   ├── analytics.py
│   ├── entity_extraction.py
│   ├── entity_store.py
│   ├── evidence_store.py
│   ├── file_loader.py
│   ├── graph_service.py
│   ├── pattern_detection.py
│   ├── preprocessing.py
│   ├── relationship_analysis.py
│   ├── relationship_store.py
│   └── report_generator.py
│
├── pages/
│   ├── dashboard.py
│   ├── evidence.py
│   ├── entities.py
│   ├── relationships.py
│   ├── assistant.py
│   └── reports.py
│
├── tests/
│   ├── test_ingestion.py
│   ├── test_entities.py
│   └── test_relationships.py
│
└── utils/
    └── helpers.py
```

---

## ⚙️ Local Setup

### Requirements

* Python 3.10+
* Windows, macOS, or Linux
* Internet connection for Ollama Cloud AI features

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Locally

```bash
streamlit run app.py
```

Then open the URL displayed in the terminal, usually:

```text
http://localhost:8501
```

### Ollama Cloud Configuration

For local development, configure the Ollama Cloud API key through environment variables or Streamlit secrets.

```text
OLLAMA_API_KEY=your_api_key
```

The API key should **never be committed to GitHub**.

---

## 🧪 Testing

Manual smoke tests were performed for the major processing components.

Current verification includes:

* Evidence ingestion: **14/14 checks passed**
* Entity extraction: **24/24 checks passed**
* Relationship analysis: **25/25 checks passed**
* PDF report generation: verified
* AI Assistant evidence-grounding flow: verified
* Streamlit Cloud deployment: verified

> Note: The current test files are manual smoke-test scripts and are not collected as pytest test cases.

---

## 🗺️ Development Roadmap

| Phase | Module                                  | Status      |
| ----- | --------------------------------------- | ----------- |
| 1     | Project setup & Streamlit UI            | ✅ Completed |
| 2     | Evidence ingestion & preprocessing      | ✅ Completed |
| 3     | NLP entity extraction                   | ✅ Completed |
| 4     | Relationship & link analysis            | ✅ Completed |
| 5     | AI Investigation Assistant              | ✅ Completed |
| 6     | Pattern / indicator detection           | ✅ Completed |
| 7     | Investigation dashboard                 | ✅ Completed |
| 8     | JSON / PDF report generation            | ✅ Completed |
| 9     | Authentication & admin roles            | ⏳ Planned   |
| 10    | Persistent cloud storage & final polish | ⏳ Planned   |

---

## 🔐 Evidence & AI Safety

The system follows an evidence-grounded approach.

The AI assistant is designed to:

1. Retrieve relevant evidence.
2. Provide that evidence as context to the AI model.
3. Generate an answer using only the supplied context.
4. Preserve Evidence IDs and record/page references where available.
5. Avoid unsupported conclusions.

AI output must always be reviewed by a human investigator.

---

## ⚠️ Limitations

This project is an **academic prototype** and has several limitations:

* It is not a certified forensic system.
* AI-generated responses require human verification.
* NLP extraction may contain classification errors.
* Pattern indicators are descriptive rather than proof of wrongdoing.
* Current evidence storage is not yet a production-grade persistent cloud database.
* Authentication and role-based access are not yet implemented.
* The system should not be used as the sole basis for legal or investigative decisions.

---

## 👩‍💻 Project

**AI Investigation Assistant**
Digital Evidence Analysis Platform — Academic Prototype

Built using Python, Streamlit, NLP, NetworkX, Ollama Cloud, and Gemma 4:31b.

**Ippo GitHub-la `README.md` open → Edit ✏️ → old content full-a replace → Commit changes.**
