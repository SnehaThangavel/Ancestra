# Ancestra Backend (SESCI Architecture)

Production-grade Python backend implementing the **SESCI** (Spatio-temporal Evolutionary Structural Consensus & Inspection) architecture for heritage monument structural monitoring using crowdsourced photography, computer vision, and PostgreSQL.

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

## 🧮 Module 2: Six-Factor Dynamic Reliability Coefficient Engine

Module 2 (`app.modules.reliability_engine.ReliabilityEngineModule`) calculates a composite reliability coefficient $R_i \in [0, 1]$ for each crowdsourced photo observation. Downstream consensus memory and anomaly validation modules use $R_i$ to weight how much each photo updates the monument's historical health state.

### Reliability Coefficient Formula

$$R_i = \sum_{k=1}^6 w_k \cdot f_k \quad \text{where} \quad \sum_{k=1}^6 w_k = 1.0, \quad R_i \in [0.0, 1.0]$$

| Factor ($f_k$) | Method Name | Description & Calculation Logic | Default Weight ($w_k$) |
| :--- | :--- | :--- | :--- |
| **1. Image Quality** ($f_{\text{quality}}$) | `compute_image_quality_factor` | Derived from Module 1's `overall_quality_score` with a non-linear power curve ($s^{1.5}$) so borderline quality photos are penalized disproportionately. | `0.25` (25%) |
| **2. Geometric Consistency** ($f_{\text{geom}}$) | `compute_geometric_consistency_factor` | Derived from ORB/RANSAC `registration_confidence`. Returns fixed floor `0.1` on registration failure to retain weak signal. | `0.20` (20%) |
| **3. Viewpoint Diversity** ($f_{\text{view}}$) | `compute_viewpoint_diversity_factor` | Compares vantage parameters (orientation, camera, source) against regional observations in a 90-day window. Rewards novel viewpoints; defaults to `0.5` if no history. | `0.10` (10%) |
| **4. Temporal Relevance** ($f_{\text{temp}}$) | `compute_temporal_relevance_factor` | Exponential decay based on observation age ($\Delta t$) and half-life: $0.15 + 0.85 \cdot \exp(-\ln(2) \cdot \frac{\Delta t}{t_{1/2}})$, retaining non-zero historical baseline weight. | `0.15` (15%) |
| **5. Environmental Similarity** ($f_{\text{env}}$) | `compute_environmental_similarity_factor` | Evaluates exposure deviation from the historical regional mean. Wild lighting swings score lower; defaults to `0.5` if $<3$ prior observations exist. | `0.10` (10%) |
| **6. Consensus Agreement** ($f_{\text{agree}}$) | `compute_agreement_factor` | Structural/histogram similarity against region's current `ConsensusState` tensor. Defaults to `1.0` for initial baseline observations. | `0.20` (20%) |

### Configuration & Weight Customization

Factor weights and decay half-life are configured in `backend/app/config.py` (and overridable via `.env`):

```python
# app/config.py
RELIABILITY_TEMPORAL_HALF_LIFE_DAYS: float = 180.0
RELIABILITY_WEIGHTS: Dict[str, float] = {
    "image_quality": 0.25,
    "geometric_consistency": 0.20,
    "viewpoint_diversity": 0.10,
    "temporal_relevance": 0.15,
    "environmental_similarity": 0.10,
    "agreement": 0.20,
}
```

A Pydantic validator (`@field_validator("RELIABILITY_WEIGHTS")`) enforces that factor weights sum to $1.0 \pm 10^{-4}$.

### API Endpoint & Automated Hook

- **Automated Upload Hook**: `ImageIngestionModule.ingest()` automatically invokes `ReliabilityEngineModule.compute_reliability()` immediately upon creating an `Observation` record in PostgreSQL.
- **Standalone Recompute Endpoint**: `POST /api/v1/reliability/score/{observation_id}` allows recomputing reliability on demand (e.g. after consensus state updates or with custom weight overrides). Protected by JWT OAuth authentication.

---

## 🧠 Module 3: Reliability-Weighted Continuous Running Consensus Memory

Module 3 (`app.modules.consensus_memory.ConsensusMemoryModule`) maintains an incrementally-updated baseline visual condition representation (`ConsensusState`) for each architectural region. Each incoming photograph updates this memory state proportionally to its Module 2 reliability score ($R_i$).

### Reliability-Adaptive Evidence Fusion Formula

$$\mathbf{T}_{t} = \frac{\mathbf{T}_{t-1} \cdot W_{t-1} + \mathbf{T}_{\text{obs}} \cdot R_i}{W_{t-1} + R_i}$$

$$W_t = W_{t-1} + R_i, \quad N_t = N_{t-1} + 1$$

Where:
- $\mathbf{T}_t$: The updated regional consensus feature tensor (normalized intensity histogram, channel means, standard deviation, and texture Laplacian variance).
- $\mathbf{T}_{\text{obs}}$: The statistical visual feature representation extracted from the newly registered photo crop.
- $W_t$: Cumulative reliability weight ($\sum R_i$).
- $R_i \in [0, 1]$: Module 2 composite reliability score of the observation.
- $N_t$: Total observation count for the active version.

This mathematical formulation guarantees that low-reliability photos barely perturb the consensus memory, while high-reliability observations update the baseline appropriately.

### Lifecycle & Versioning Mechanism

1. **Cold-Start Initialization (`initialize_consensus_state`)**:
   - The first-ever observation for a region initializes **Version 1** with $W = R_1$, $N = 1$, `structural_health_index = 1.0` (assumed pristine), and baseline feature tensor $\mathbf{T}_1 = \mathbf{T}_{\text{obs}}$.
2. **Incremental Running Updates (`update_consensus_state`)**:
   - Subsequent observations update the active `ConsensusState` row in place, blending feature tensors and incrementing $W$ and $N$.
   - `structural_health_index` is preserved and untouched by consensus memory (health assessment is handled downstream by Module 4: Anomaly Validation).
3. **Major Recalibration & Version Reset (`create_new_consensus_version`)**:
   - Following verified conservation/restoration work, a new version ($V_{k+1}$) is created via `POST /api/v1/consensus/{region_id}/reset`.
   - Resets $W=0.0$, $N=0$, $\mathbf{T}=\text{null}$ (to be populated by the next post-restoration photo), while retaining historical versions in the database.

### API Endpoints

- `GET /api/v1/consensus/{region_id}`: Retrieve active consensus memory tensor, version, and health metrics for a region.
- `POST /api/v1/consensus/update`: Manually incorporate an observation into regional consensus memory.
- `POST /api/v1/consensus/{region_id}/reset`: Increment consensus version following structural restoration, logging the `reset_reason`.



---

## 🗄️ Database Architecture (PostgreSQL, UUID, & JSONB)

Ancestra uses **PostgreSQL** for its persistent database layer, leveraging native PostgreSQL features for scalability, geospatial and telemetry analysis, and data integrity:

- **UUID Primary Keys**: All tables use `UUID` (v4) primary keys via `sqlalchemy.dialects.postgresql.UUID(as_uuid=True)` for distributed uniqueness across crowdsourced clients.
- **Native JSONB Columns**: High-speed binary JSON (`JSONB`) is utilized for semi-structured metadata:
  - `observations.exif_data` (indexed via a PostgreSQL **GIN index** for fast key/value queries)
  - `observations.reliability_factors`
  - `regions.bounding_box` and `regions.reference_features`
  - `consensus_states.consensus_tensor`
  - `anomaly_validations.defect_polygon`
  - `evidence_logs.payload`
- **PostgreSQL Arrays**: `anomaly_validations.corroborating_observation_ids` uses native `ARRAY(UUID)` to track corroborating crowd observations without complex join overhead.
- **Integrity Constraints & Triggers**:
  - Check constraints for metrics: `structural_health_index` $\in [0.0, 1.0]$, `severity_score` $\in [0.0, 1.0]$, `urgency_index` $\in [0.0, 1.0]$.
  - Unique constraint on `(work_order_id, block_index)` for immutable cryptographic hash chaining on `evidence_logs`.
  - Database triggers execute `update_updated_at_column()` on `UPDATE` operations.

### Table Schema Summary

1. **`monuments`**: Core heritage site asset records (UUID `id`, `name`, `location_name`, `latitude`, `longitude`, `heritage_status`, `importance_tier`, timestamps).
2. **`regions`**: Architectural sub-components (`monument_id` FK, `name`, `category`, `bounding_box` JSONB, `reference_features` JSONB).
3. **`observations`**: Crowdsourced photo submissions (`monument_id` FK, `region_id` FK, image quality triage scores, `exif_data` JSONB with GIN index, registration metadata, `reliability_factors` JSONB).
4. **`consensus_states`**: Continuous running Bayesian state per region (`region_id` FK, `consensus_tensor` JSONB, `cumulative_reliability`, `structural_health_index` [0, 1]).
5. **`anomaly_validations`**: Validated defects (`region_id` FK, `anomaly_type`, `ssim_delta`, `severity_score` [0, 1], `corroborating_observation_ids` ARRAY(UUID), `defect_polygon` JSONB).
6. **`work_orders`**: Prioritized conservation dispatches (`validation_id` FK, `urgency_index` [0, 1], `status`, `assigned_team`, `recommended_action`).
7. **`evidence_logs`**: Immutable SHA-256 hash-chained audit blocks (`work_order_id` FK, `block_index`, `previous_hash`, `current_hash`, `payload` JSONB, unique on `(work_order_id, block_index)`).

---

## 🚀 Setup & Execution

### 1. PostgreSQL Database Initialization

Ensure PostgreSQL 15+ is installed and running locally:

```sql
-- Connect via psql:
CREATE USER ancestra_user WITH PASSWORD 'ancestra_password';
CREATE DATABASE ancestra_db OWNER ancestra_user;
CREATE DATABASE ancestra_test_db OWNER ancestra_user;
GRANT ALL PRIVILEGES ON DATABASE ancestra_db TO ancestra_user;
GRANT ALL PRIVILEGES ON DATABASE ancestra_test_db TO ancestra_user;
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure connection strings:

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_db
TEST_DATABASE_URL=postgresql://ancestra_user:ancestra_password@localhost:5432/ancestra_test_db
```

### 3. Migrations (Alembic)

Apply database migrations:

```bash
# Apply migrations to primary database
alembic upgrade head
```

To recreate or inspect the schema:

```bash
# Check current migration revision
alembic current

# Rollback and re-apply
alembic downgrade base
alembic upgrade head
```

### 4. Running the Application

```bash
# Start FastAPI server with live reload
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 🧪 Testing with Isolated Test Database

Tests run against the dedicated `ancestra_test_db` PostgreSQL database:

```bash
# Run full test suite with pytest
pytest tests -v
```

### Recreating the Test Database

If you ever need to reset the test database from scratch:

```sql
DROP DATABASE IF EXISTS ancestra_test_db;
CREATE DATABASE ancestra_test_db OWNER ancestra_user;
GRANT ALL PRIVILEGES ON DATABASE ancestra_test_db TO ancestra_user;
```

The test runner automatically creates all required tables and executes tests within transactional rollbacks for complete isolation.
