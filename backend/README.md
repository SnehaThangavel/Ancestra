# Ancestra Backend (SESCI Architecture)

Production-grade Python backend implementing the **SESCI** (Spatio-temporal Evolutionary Structural Consensus & Inspection) architecture for heritage monument structural monitoring using crowdsourced photography and computer vision.

---

## 🏛️ Module-to-Patent-Claim Architecture Mapping

| Module | System Component | Patent Claim Scope & Core Responsibility |
| :--- | :--- | :--- |
| **Module 1: Ingestion & Registration** | `app.modules.ingestion` | Automated image quality triage (blur/glare check), EXIF extraction, ORB feature matching, homography estimation, and perspective alignment against baseline monument geometries. |
| **Module 2: Reliability Engine** | `app.modules.reliability_engine` | Dynamic multi-factor reliability scoring calculating $R_i \in [0, 1]$ across sensor fidelity, lighting conditions, vantage perspective angle, crowd credibility history, temporal relevance, and registration confidence. |
| **Module 3: Consensus Memory** | `app.modules.consensus_memory` | Reliability-weighted continuous running Bayesian update of regional consensus representations ($C_t$), preserving true historical state while dampening transient anomalies. |
| **Module 4: Anomaly Validation** | `app.modules.validation` | Multi-scale structural similarity (SSIM) anomaly detection, morphological edge deltas, crack/spalling localization, and multi-observer corroboration filtering. |
| **Module 5: Temporal Evolution** | `app.modules.temporal_evolution` | Time-series trend analysis, deterioration velocity rate computation ($\frac{dD}{dt}$), defect growth extrapolation, and risk horizon forecasting. |
| **Module 6: Orchestration & Dispatch** | `app.modules.orchestrator` | Multi-criteria urgency index scoring, automated conservation work-order generation, priority dispatching, and immutable SHA-256 hash-chained evidence log generation. |
| **AI Upgrade: Foundation Models** | `app.ai` | Segment Anything Model (SAM) zero-shot architectural boundary segmentation and OpenCLIP semantic classification of monument components. |

---

## 📂 Backend Directory Structure

```text
backend/
├── app/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── config.py                # Settings, env vars, model paths
│   ├── database.py              # SQLAlchemy engine/session setup
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── observation.py       # Raw photo + metadata records
│   │   ├── region.py            # Architectural region records
│   │   ├── consensus_state.py   # Per-region consensus memory state
│   │   ├── validation.py        # Validated anomaly findings
│   │   └── work_order.py        # Conservation work orders + evidence log
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── ingestion.py
│   │   ├── reliability.py
│   │   ├── consensus.py
│   │   ├── validation.py
│   │   ├── temporal.py
│   │   └── orchestrator.py
│   ├── modules/                 # Six core SESCI patent modules
│   │   ├── ingestion.py
│   │   ├── reliability_engine.py
│   │   ├── consensus_memory.py
│   │   ├── validation.py
│   │   ├── temporal_evolution.py
│   │   └── orchestrator.py
│   ├── ai/                      # AI segmentation upgrade (SAM + CLIP)
│   │   ├── sam_segmenter.py
│   │   ├── region_classifier.py
│   │   └── model_weights/       # Local SAM / CLIP weights (gitignored)
│   ├── routers/                 # FastAPI route handlers
│   │   ├── ingestion.py
│   │   ├── consensus.py
│   │   ├── validation.py
│   │   ├── temporal.py
│   │   └── orchestrator.py
│   └── utils/
│       ├── image_utils.py       # Shared OpenCV/PIL helpers
│       └── logging.py
├── tests/                       # Test suite mirroring app/ structure
├── alembic/                     # Database migrations
├── requirements.txt             # Pinned dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Ignores weights, caches, envs, sqlite
└── README.md                    # Module documentation & patent mapping
```

---

## 🚀 Setup & Execution (Scaffolding)

```bash
# 1. Navigate to backend directory
cd backend

# 2. Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Run FastAPI development server
uvicorn app.main:app --reload --port 8000
```
