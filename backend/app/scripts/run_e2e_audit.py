"""Audit script: Run live E2E flow against real database for region 57f11112-75b1-4e1d-80ff-e04f833ccc08."""

import io
import os
import sys
import uuid
import numpy as np
import cv2
from datetime import datetime, timezone

# Ensure backend root on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.monument import Monument
from app.models.region import Region
from app.models.consensus_state import ConsensusState
from app.models.user import User
from app.auth.jwt_handler import create_access_token

def ensure_test_fixtures(db):
    # Ensure test user
    user = db.query(User).filter(User.email == "auditor@asi.gov.in").first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="auditor@asi.gov.in",
            name="Conservation Auditor",
            google_sub_id="google_sub_auditor_001",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    target_region_id = uuid.UUID("57f11112-75b1-4e1d-80ff-e04f833ccc08")
    region = db.query(Region).filter(Region.id == target_region_id).first()
    if not region:
        # Check if Shore Temple monument exists
        monument = db.query(Monument).filter(Monument.name.ilike("%Shore Temple%")).first()
        if not monument:
            monument = Monument(
                id=uuid.uuid4(),
                name="Shore Temple, Mahabalipuram",
                location_name="Mahabalipuram, Tamil Nadu",
                latitude=12.6167,
                longitude=80.1983,
                heritage_status="UNESCO World Heritage Site",
                importance_tier=1,
            )
            db.add(monument)
            db.commit()
            db.refresh(monument)

        region = Region(
            id=target_region_id,
            monument_id=monument.id,
            name="East-Facing Rajasimhesvara Vimana",
            category="vimana",
            bounding_box=[100, 100, 400, 400],
        )
        db.add(region)
        db.commit()
        db.refresh(region)

    # Ensure baseline ConsensusState
    cs = db.query(ConsensusState).filter(ConsensusState.region_id == target_region_id).first()
    if not cs:
        cs = ConsensusState(
            id=uuid.uuid4(),
            region_id=target_region_id,
            version=1,
            observation_count=0,
            structural_health_index=1.0,
        )
        db.add(cs)
        db.commit()

    return user, region.monument_id, target_region_id


def generate_synthetic_images():
    # Baseline image: 600x600 stone texture pattern
    np.random.seed(42)
    base_img = np.full((600, 600, 3), 160, dtype=np.uint8)
    # Add high-contrast feature points for ORB matching
    for i in range(50, 550, 40):
        for j in range(50, 550, 40):
            cv2.circle(base_img, (i, j), 4, (80, 80, 80), -1)
            cv2.rectangle(base_img, (i+5, j+5), (i+15, j+15), (200, 200, 200), 1)

    # Defect image: clone baseline, draw prominent crack / spalling zone
    defect_img = base_img.copy()
    # Draw large jagged crack across the center
    pts = np.array([[200, 200], [250, 280], [300, 310], [380, 400], [420, 480]], np.int32)
    cv2.polylines(defect_img, [pts], isClosed=False, color=(20, 20, 20), thickness=8)
    # Add dark spalling patch
    cv2.circle(defect_img, (320, 320), 45, (30, 30, 30), -1)

    _, base_bytes = cv2.imencode(".jpg", base_img)
    _, defect_bytes = cv2.imencode(".jpg", defect_img)

    return base_bytes.tobytes(), defect_bytes.tobytes()


def run_e2e_audit():
    db = SessionLocal()
    user, monument_id, region_id = ensure_test_fixtures(db)
    token = create_access_token(user_id=user.id, email=user.email)
    headers = {"Authorization": f"Bearer {token}"}

    client = TestClient(app)
    base_bytes, defect_bytes = generate_synthetic_images()

    print("==================================================")
    print("ANCESTRA E2E AUDIT EXECUTION")
    print(f"Target Monument ID: {monument_id}")
    print(f"Target Region ID: {region_id}")
    print("==================================================")

    # 1. suggest-region
    print("\n[Step 1] POST /api/v1/ingestion/suggest-region")
    resp1 = client.post(
        "/api/v1/ingestion/suggest-region",
        headers=headers,
        data={"monument_id": str(monument_id)},
        files={"file": ("test_photo.jpg", base_bytes, "image/jpeg")},
    )
    print(f"Status: {resp1.status_code}")
    print(f"Response: {resp1.json()}")

    # 2. upload baseline photo
    print("\n[Step 2] POST /api/v1/ingestion/upload (Baseline Photo)")
    resp2 = client.post(
        "/api/v1/ingestion/upload",
        headers=headers,
        data={
            "monument_id": str(monument_id),
            "region_id": str(region_id),
            "user_id": str(user.id),
        },
        files={"file": ("baseline_photo.jpg", base_bytes, "image/jpeg")},
    )
    print(f"Status: {resp2.status_code}")
    baseline_data = resp2.json()
    baseline_obs_id = baseline_data.get("observation_id")
    print(f"Baseline Obs ID: {baseline_obs_id}")
    print(f"Quality Valid: {baseline_data.get('is_valid_quality')}, Score: {baseline_data.get('quality_assessment', {}).get('overall_quality_score')}")

    # 3. upload second photo with visible structural damage
    print("\n[Step 3] POST /api/v1/ingestion/upload (Second Photo with Damage)")
    resp3 = client.post(
        "/api/v1/ingestion/upload",
        headers=headers,
        data={
            "monument_id": str(monument_id),
            "region_id": str(region_id),
            "user_id": str(user.id),
        },
        files={"file": ("damaged_photo.jpg", defect_bytes, "image/jpeg")},
    )
    print(f"Status: {resp3.status_code}")
    defect_data = resp3.json()
    defect_obs_id = defect_data.get("observation_id")
    print(f"Damaged Obs ID: {defect_obs_id}")
    print(f"Registration Confidence: {defect_data.get('registration_confidence')}")

    # 4. validation (SSIM comparison against baseline)
    print(f"\n[Step 4] POST /api/v1/validation/verify (Observation: {defect_obs_id})")
    resp4 = client.post(
        "/api/v1/validation/verify",
        headers=headers,
        json={
            "observation_id": defect_obs_id,
            "region_id": str(region_id),
            "ssim_threshold": 0.90,
        },
    )
    print(f"Status: {resp4.status_code}")
    val_data = resp4.json()
    print(f"SSIM Score: {val_data.get('ssim_score')}")
    print(f"SSIM Delta: {val_data.get('ssim_delta')}")
    print(f"Anomaly Detected: {val_data.get('anomaly_detected')}")
    print(f"Severity Score: {val_data.get('severity_score')}")
    print(f"Anomaly Type: {val_data.get('anomaly_type')}")
    print(f"Defect Bounding Boxes: {val_data.get('defect_bounding_boxes')}")
    validation_id = val_data.get("validation_id")

    # 5. temporal trend (Module 5)
    print(f"\n[Step 5] GET /api/v1/temporal/region/{region_id}")
    resp5 = client.get(
        f"/api/v1/temporal/region/{region_id}",
        headers=headers,
    )
    print(f"Status: {resp5.status_code}")
    trend_data = resp5.json()
    print(f"Trend Status: {trend_data.get('status')}")
    print(f"Record Count: {trend_data.get('record_count')}")
    print(f"Trend Classification: {trend_data.get('trend_classification')}")
    print(f"Rate Per Day: {trend_data.get('deterioration_rate_per_day')}")
    print(f"Confidence Note: {trend_data.get('confidence_note')}")

    # 6. work order creation (Module 6)
    print("\n[Step 6] POST /api/v1/orchestrator/work-orders")
    resp6 = client.post(
        "/api/v1/orchestrator/work-orders",
        headers=headers,
        json={
            "region_id": str(region_id),
            "validation_id": validation_id,
            "assigned_team": "ASI Southern Circle Urgent Response",
            "recommended_action": "Immediate structural crack stabilization and telemetry sensor install.",
        },
    )
    print(f"Status: {resp6.status_code}")
    wo_data = resp6.json()
    work_order_id = wo_data.get("id")
    print(f"Work Order ID: {work_order_id}")
    print(f"Urgency Index: {wo_data.get('urgency_index')}")
    print(f"Status: {wo_data.get('status')}")

    # 7. audit chain verify (Module 6)
    print(f"\n[Step 7] GET /api/v1/orchestrator/work-orders/{work_order_id}/verify-chain")
    resp7 = client.get(
        f"/api/v1/orchestrator/work-orders/{work_order_id}/verify-chain",
        headers=headers,
    )
    print(f"Status: {resp7.status_code}")
    chain_data = resp7.json()
    print(f"Chain Valid: {chain_data.get('is_valid')}")
    print(f"Block Count: {chain_data.get('block_count')}")
    print(f"Genesis Hash: {chain_data.get('genesis_hash')}")
    print(f"Head Hash: {chain_data.get('head_hash')}")
    print(f"Audit Message: {chain_data.get('message')}")

    db.close()


if __name__ == "__main__":
    run_e2e_audit()
