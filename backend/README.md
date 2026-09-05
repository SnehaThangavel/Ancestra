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
