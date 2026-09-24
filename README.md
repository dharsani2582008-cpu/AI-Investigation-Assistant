# AI Investigation Assistant

An academic prototype web application that helps investigators analyze
digital evidence (CSV, Excel, JSON, PDF) using NLP-based entity
extraction, relationship/link analysis, a local AI assistant, and
report generation.

**This is a college project prototype.** It is NOT a certified
forensic tool and its output is NOT legally admissible. All
AI-generated findings require investigator verification.

## Status

Currently in **Phase 1**: project structure, Streamlit shell, sidebar
navigation, dashboard placeholder, and evidence upload interface with
basic file validation.

## Requirements

- Python 3.10+
- Windows, macOS, or Linux

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the URL shown in the terminal (usually http://localhost:8501).

## Project Structure

```
AI-Investigation-Assistant/
├── app.py                  # Main entry point + sidebar navigation
├── requirements.txt
├── data/
│   ├── uploads/             # Raw uploaded evidence
│   ├── processed/           # Cleaned/processed evidence (later phases)
│   └── sample/              # Synthetic demo data (later phases)
├── database/                # SQLite storage (later phases)
├── services/                # File loading, NLP, relationship logic (later phases)
├── models/                  # Data schemas (later phases)
├── utils/
│   ├── config.py             # Central configuration/constants
│   └── helpers.py            # Shared helper functions
├── pages/
│   ├── dashboard.py
│   ├── evidence.py
│   ├── entities.py           # Placeholder until Phase 3
│   ├── relationships.py       # Placeholder until Phase 4
│   ├── assistant.py           # Placeholder until Phase 5
│   └── reports.py             # Placeholder until Phase 8
└── assets/
```

## Roadmap

1. ✅ Project setup, dashboard placeholder, evidence upload
2. Evidence ingestion (CSV/Excel/JSON/PDF parsing + preprocessing)
3. NLP entity extraction
4. Relationship/link engine + graph visualization
5. Local AI assistant (Ollama + Llama 3)
6. Pattern/anomaly detection
7. Full dashboard with real metrics
8. Report generation (PDF/Excel)
9. Authentication + admin roles
10. Testing, sample data, and polish
