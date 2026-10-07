# Ancestra Backend

Production-grade FastAPI backend for **Ancestra**, an AI-assisted heritage monument structural monitoring platform designed for conservation experts and archaeologists.

---

## 🏛️ System Architecture (Expert-Upload Flow)

The current Ancestra architecture is centered around **expert-directed photo ingestion and structural inspection**:

```
[Expert Photo Upload]
         │
         ▼
[Module 1: Ingestion & Registration]
  ├── Image Quality Triage (Laplacian Blur Variance & Exposure/Glare Ratio)
  ├── EXIF Metadata Extraction (Camera, Timestamp, GPS)
  ├── AI Region Suggestion (SAM Segmenter + OpenCLIP Classifier)
  └── Sequential Alignment (ORB Feature Matching & RANSAC Homography against prior observation)
         │
         ▼
[Module 4: Anomaly Validation & Detection]
  ├── Multi-Scale Structural Similarity (SSIM) Delta Analysis against Baseline
  ├── Lithic Defect Localization (Crack / Spalling Bounding Box Generation)
  └── Severity Scoring & Anomaly Type Classification
         │
         ▼
[Module 5: Temporal Evolution]
  ├── Historical Severity Time-Series Tracking
  └── Deterioration Velocity Rate Computation (dD/dt)
         │
         ▼
[Module 6: Work Order Orchestration]
  ├── Multi-Criteria Urgency Index Calculation
  ├── Conservation Action Plan & Work Order Dispatch
  └── Immutable SHA-256 Hash-Chained Evidence Audit Trail (Genesis & Audit Blocks)
```

### Active Core Modules

| Module | Python Path | Responsibilities in Current Flow |
| :--- | :--- | :--- |
| **Module 1: Ingestion & Registration** | `app.modules.ingestion` | Image decoding, quality filtering (blur/glare thresholds), EXIF parsing, AI-assisted zero-shot region suggestion, and sequential ORB/RANSAC alignment. |
| **Module 4: Anomaly Validation** | `app.modules.validation` | Multi-scale SSIM comparison against baseline observation, structural anomaly thresholding, defect bounding box extraction, and severity scoring. |
| **Module 5: Temporal Evolution** | `app.modules.temporal_evolution` | Time-series regression over regional damage observations, deterioration velocity rate ($\frac{dD}{dt}$) calculation, and trend estimation. |
| **Module 6: Orchestration & Dispatch** | `app.modules.orchestrator` | Composite urgency scoring based on severity and importance tier, work order lifecycle management, and SHA-256 hash-chained evidence logs. |
| **AI Foundation Models** | `app.ai` | Segment Anything Model (SAM `vit_b`) for architectural boundary mask segmentation and OpenCLIP (`ViT-B/32`) for component classification. |
| **Authentication & Auth** | `app.routers.auth` | Google OAuth 2.0 handshake, user management, and JWT access/refresh token rotation. |

---

## ⚙️ Setup & Model Weights

### 1. SAM Model Checkpoint Download

The AI region suggestion feature uses Meta AI's **Segment Anything Model (SAM)** `vit_b` architecture.

Download the official checkpoint and place it in the `backend/model_weights` directory:

```bash
# From the backend directory
mkdir -p model_weights
curl -L -o model_weights/sam_vit_b_01ec64.pth https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

- **File Path**: `backend/model_weights/sam_vit_b_01ec64.pth`
- **Expected Architecture**: ViT-B (`vit_b`)

### What happens if the SAM checkpoint is missing?

- **When AI segmentation is invoked**: If `USE_AI_SEGMENTATION=True` and the checkpoint is not found at `settings.SAM_CHECKPOINT_PATH`, `SAMSegmenter.load_model()` logs an error and raises a `FileNotFoundError` with download instructions.
- **Graceful Fallback**: If `USE_AI_SEGMENTATION=False` (set via `.env`), or when the expert selects the architectural region directly from the registered list, ingestion bypasses SAM segmentation and performs standard homography alignment against the region's latest baseline without requiring model weights.

---

## 🗄️ Database Architecture (PostgreSQL, UUID, & JSONB)

Ancestra uses **PostgreSQL 15+** with SQLAlchemy ORM and Alembic migrations:

- **UUID Primary Keys**: All tables utilize UUID (v4) primary keys for unique distributed entity identification.
- **JSONB Metadata**: EXIF headers, bounding boxes, defect polygons, and cryptographic audit payloads are stored in native PostgreSQL `JSONB` columns with GIN indexing for fast queries.
- **Cryptographic Audit Log**: `evidence_logs` table enforces an immutable block sequence per work order with `(work_order_id, block_index)` uniqueness and previous-hash verification.

### Database Entities

1. **`monuments`**: Monitored heritage structures (name, location, coordinates, heritage status, importance tier).
2. **`regions`**: Architectural components belonging to a monument (name, category, bounding box).
3. **`observations`**: Photographic inspection records with quality scores, EXIF metadata, and registration metrics.
4. **`anomaly_validations`**: SSIM delta records, severity scores, anomaly types, and defect bounding boxes.
5. **`work_orders`**: Actionable conservation work orders with urgency indices and assigned field teams.
6. **`evidence_logs`**: SHA-256 hash-chained audit blocks for verifiable tamper-evident compliance.
7. **`users`**: Authenticated conservation experts and administrative users.

---

## 🚀 Installation & Local Execution

### 1. Database Initialization

```sql
CREATE USER ancestra_user WITH PASSWORD 'ancestra_password';
CREATE DATABASE ancestra_db OWNER ancestra_user;
CREATE DATABASE ancestra_test_db OWNER ancestra_user;
GRANT ALL PRIVILEGES ON DATABASE ancestra_db TO ancestra_user;
GRANT ALL PRIVILEGES ON DATABASE ancestra_test_db TO ancestra_user;
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

Key environment variables in `.env`:

```env
DATABASE_URL=postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_db
TEST_DATABASE_URL=postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_test_db
SAM_CHECKPOINT_PATH=model_weights/sam_vit_b_01ec64.pth
SAM_MODEL_TYPE=vit_b
USE_AI_SEGMENTATION=true
JWT_SECRET_KEY=your-secure-jwt-secret
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
```

### 3. Database Migrations

```bash
alembic upgrade head
```

### 4. Running the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🧪 Testing

Run test suites against the isolated test database:

```bash
pytest tests -v
```

---

## 🔮 Planned / Not Implemented in Current Flow

The following experimental features and algorithmic modules exist in the codebase for research reference but are **not part of the active expert inspection flow**:

1. **Continuous Running Bayesian Tensor Blending (`ConsensusMemoryModule`)**:
   - Continuous weighted merging of multi-channel histogram and texture feature tensors across unverified crowd uploads ($T_t = \frac{T_{t-1} W_{t-1} + T_{obs} R_i}{W_{t-1} + R_i}$).
   - The current expert flow uses explicit pairwise observation-to-baseline SSIM comparisons instead of continuous feature tensor blending.

2. **Crowdsourced Multi-Observer Corroboration**:
   - Clustering unverified observations from multiple independent crowd contributors within spatial-temporal windows before confirming structural anomalies.
   - The current production pipeline processes verified expert submissions directly.

3. **Automated Reliability Scoring Hook in Ingestion**:
   - `auto_score_reliability` in `ImageIngestionModule.ingest()` is set to `False` by default for expert uploads, reserving Module 2 reliability scoring for crowdsourced or multi-vantage datasets.
