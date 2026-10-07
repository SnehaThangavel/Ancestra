"""Module 6: Multi-Criteria Urgency Scoring, Work Order Dispatch, and Hash-Chained Evidence Logging.

SESCI Architecture - Module 6 (Orchestrator):
Aggregates structural health indicators (Module 3), anomaly severity scores (Module 4),
and deterioration trajectories (Module 5) to compute multi-criteria urgency scores,
dispatch conservation work orders, and append tamper-evident SHA-256 hash-chained
evidence log blocks for complete audit traceability.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session

from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.models.region import Region
from app.models.work_order import WorkOrder, EvidenceLog
from app.modules.temporal_evolution import get_temporal_evolution
from app.utils.logging import get_logger

logger = get_logger(__name__)


class OrchestratorModule:
    """Calculates multi-criteria urgency score, dispatches work orders, and appends cryptographically sealed evidence entries."""

    def __init__(self) -> None:
        """Initialize orchestration engine."""
        self.temporal_service = get_temporal_evolution()

    @staticmethod
    def _resolve_uuid(val: Union[uuid.UUID, str, Any]) -> uuid.UUID:
        """Helper to cast ID into standard UUID object."""
        if isinstance(val, uuid.UUID):
            return val
        return uuid.UUID(str(val))

    # -------------------------------------------------------------------------
    # 1. Multi-Criteria Urgency Scoring
    # -------------------------------------------------------------------------
    def compute_urgency_score(
        self,
        region_id: Union[uuid.UUID, str],
        db: Session,
    ) -> Dict[str, Any]:
        """Compute composite urgency priority index and categorical level for an architectural region.

        Combines:
            1. Latest validation severity score (40% weight)
            2. Regional structural health deficit: 1.0 - health_index (35% weight)
            3. Temporal deterioration trend velocity & trajectory factor (25% weight)

        Args:
            region_id: Unique identifier for the architectural region.
            db: SQLAlchemy database session.

        Returns:
            Dict[str, Any]: Numeric urgency score in [0.0, 1.0], categorical level
                ('low', 'medium', 'high', 'critical'), and factor breakdown.
        """
        region_uuid = self._resolve_uuid(region_id)

        # 1. Fetch region metadata
        region = db.query(Region).filter(Region.id == region_uuid).first()
        region_name = region.name if region else str(region_uuid)

        # 2. Fetch active ConsensusState for structural health index
        active_consensus = (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == region_uuid)
            .order_by(ConsensusState.version.desc())
            .first()
        )
        health_index = (
            float(active_consensus.structural_health_index)
            if active_consensus and active_consensus.structural_health_index is not None
            else 1.0
        )
        health_deficit = max(0.0, min(1.0, 1.0 - health_index))

        # 3. Fetch latest AnomalyValidation record
        latest_val = (
            db.query(AnomalyValidation)
            .filter(AnomalyValidation.region_id == region_uuid)
            .order_by(AnomalyValidation.created_at.desc())
            .first()
        )
        severity_score = float(latest_val.severity_score) if latest_val else 0.0
        anomaly_type = latest_val.anomaly_type if latest_val else "none"

        # 4. Fetch temporal trend analysis from Module 5
        trend_res = self.temporal_service.estimate_deterioration_rate(region_uuid, db=db)
        trend_class = trend_res.get("trend_classification", "stable")
        rate_per_day = trend_res.get("deterioration_rate_per_day", 0.0)

        # Formulate trend acceleration factor in [0.0, 1.0]
        if trend_class == "increasing":
            trend_factor = min(1.0, 0.75 + max(0.0, rate_per_day * 10.0))
        elif trend_class == "decreasing":
            trend_factor = 0.10
        elif trend_class == "insufficient_data":
            trend_factor = 0.40
        else:  # stable
            trend_factor = 0.30

        # 5. Calculate composite weighted urgency score in [0.0, 1.0]
        # Formula: 40% Severity + 35% Health Deficit + 25% Trend Acceleration
        raw_urgency = (0.40 * severity_score) + (0.35 * health_deficit) + (0.25 * trend_factor)
        urgency_score = round(max(0.0, min(1.0, raw_urgency)), 4)

        # 6. Categorize urgency level
        if urgency_score >= 0.70:
            urgency_level = "critical"
        elif urgency_score >= 0.45:
            urgency_level = "high"
        elif urgency_score >= 0.20:
            urgency_level = "medium"
        else:
            urgency_level = "low"

        return {
            "region_id": str(region_uuid),
            "region_name": region_name,
            "urgency_score": urgency_score,
            "urgency_level": urgency_level,
            "latest_validation_id": str(latest_val.id) if latest_val else None,
            "latest_anomaly_type": anomaly_type,
            "severity_score": severity_score,
            "structural_health_index": health_index,
            "health_deficit": round(health_deficit, 4),
            "trend_classification": trend_class,
            "deterioration_rate_per_day": rate_per_day,
            "trend_factor": round(trend_factor, 4),
            "rationale": (
                f"Urgency {urgency_level.upper()} ({urgency_score:.3f}) computed from severity {severity_score:.2f}, "
                f"health deficit {health_deficit:.2f}, and {trend_class} trend trajectory."
            ),
        }

    # -------------------------------------------------------------------------
    # 2. Work Order Generation & Dispatch
    # -------------------------------------------------------------------------
    def generate_work_order(
        self,
        region_id: Union[uuid.UUID, str],
        db: Session,
        description: Optional[str] = None,
        validation_id: Optional[Union[uuid.UUID, str]] = None,
        assigned_team: Optional[str] = None,
    ) -> WorkOrder:
        """Create and dispatch a conservation work order with initial evidence log block.

        Args:
            region_id: Unique identifier for architectural region.
            db: SQLAlchemy database session.
            description: Optional custom work order action description.
            validation_id: Optional specific triggering validation ID.
            assigned_team: Optional assigned conservation team name.

        Returns:
            WorkOrder: Created and persisted WorkOrder model instance.
        """
        region_uuid = self._resolve_uuid(region_id)

        # 1. Resolve validation record
        if validation_id is not None:
            val_uuid = self._resolve_uuid(validation_id)
            validation = db.query(AnomalyValidation).filter(AnomalyValidation.id == val_uuid).first()
        else:
            validation = (
                db.query(AnomalyValidation)
                .filter(AnomalyValidation.region_id == region_uuid)
                .order_by(AnomalyValidation.created_at.desc())
                .first()
            )

        if not validation:
            raise ValueError(f"No anomaly validation record found for region '{region_id}' to attach work order.")

        # 2. Compute urgency score & level
        urgency_data = self.compute_urgency_score(region_uuid, db=db)
        urgency_score = urgency_data["urgency_score"]
        urgency_level = urgency_data["urgency_level"]

        # 3. Determine recommended action / description
        region = db.query(Region).filter(Region.id == region_uuid).first()
        region_name = region.name if region else "Architectural Zone"

        if description and description.strip():
            recommended_action = description.strip()
        else:
            anomaly_label = validation.anomaly_type.replace("_", " ").title() if validation.anomaly_type else "Structural Defect"
            if urgency_level in ["critical", "high"]:
                recommended_action = (
                    f"[{urgency_level.upper()} URGENCY] {anomaly_label} detected (Severity: {validation.severity_score:.2f}) "
                    f"on {region_name}. Immediate on-site structural shoring, ultrasonic tomography, and stabilization required."
                )
            else:
                recommended_action = (
                    f"[{urgency_level.upper()} URGENCY] {anomaly_label} observed (Severity: {validation.severity_score:.2f}) "
                    f"on {region_name}. Routine monitoring and non-invasive conservation intervention scheduled."
                )

        # 4. Create and persist WorkOrder
        work_order = WorkOrder(
            validation_id=validation.id,
            urgency_index=urgency_score,
            status="pending",
            assigned_team=assigned_team or "ASI Regional Conservation Unit",
            recommended_action=recommended_action,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        # 5. Append Genesis block to cryptographic EvidenceLog
        self.create_evidence_log_entry(
            work_order_id=work_order.id,
            db=db,
            event_type="work_order_dispatched",
            details={
                "work_order_id": str(work_order.id),
                "region_id": str(region_uuid),
                "region_name": region_name,
                "validation_id": str(validation.id),
                "anomaly_type": validation.anomaly_type,
                "severity_score": validation.severity_score,
                "urgency_score": urgency_score,
                "urgency_level": urgency_level,
                "assigned_team": work_order.assigned_team,
                "recommended_action": recommended_action,
            },
        )

        logger.info(
            f"Dispatched WorkOrder ID {work_order.id} for Region ID {region_uuid} (Urgency: {urgency_score:.3f} - {urgency_level})"
        )
        return work_order

    # -------------------------------------------------------------------------
    # 3. Cryptographic SHA-256 Hash-Chained Evidence Logging
    # -------------------------------------------------------------------------
    def create_evidence_log_entry(
        self,
        work_order_id: Union[uuid.UUID, str],
        db: Session,
        event_type: str,
        details: Dict[str, Any],
    ) -> EvidenceLog:
        """Append an immutable SHA-256 hash-chained block to the work order evidence audit trail.

        Args:
            work_order_id: Unique identifier of target work order.
            db: SQLAlchemy database session.
            event_type: Audit event classification string (e.g. 'work_order_dispatched', 'inspection_completed').
            details: Serializable dictionary containing event payload metadata.

        Returns:
            EvidenceLog: Persisted hash-chained audit log block.
        """
        wo_uuid = self._resolve_uuid(work_order_id)

        # 1. Fetch latest block for this work order to establish hash chain
        latest_block = (
            db.query(EvidenceLog)
            .filter(EvidenceLog.work_order_id == wo_uuid)
            .order_by(EvidenceLog.block_index.desc())
            .first()
        )

        if latest_block is None:
            block_index = 0
            previous_hash = "0" * 64  # Genesis block pointer
        else:
            block_index = latest_block.block_index + 1
            previous_hash = latest_block.current_hash

        # 2. Assemble canonical payload snapshot
        timestamp_str = datetime.now(timezone.utc).isoformat()
        payload_data = {
            "event_type": event_type,
            "details": details,
            "timestamp": timestamp_str,
            "block_index": block_index,
        }

        # 3. Compute deterministic canonical SHA-256 hash
        # Formula: H_i = SHA-256( work_order_id || block_index || previous_hash || canonical_json_payload )
        canonical_json = json.dumps(payload_data, sort_keys=True)
        raw_block_str = f"{str(wo_uuid)}:{block_index}:{previous_hash}:{canonical_json}"
        current_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()

        # 4. Persist EvidenceLog block
        log_entry = EvidenceLog(
            work_order_id=wo_uuid,
            block_index=block_index,
            previous_hash=previous_hash,
            current_hash=current_hash,
            payload=payload_data,
            created_at=datetime.now(timezone.utc),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)

        logger.info(
            f"Appended EvidenceLog block #{block_index} for WorkOrder {wo_uuid} (hash: {current_hash[:16]}...)"
        )
        return log_entry

    def verify_evidence_chain(
        self,
        work_order_id: Union[uuid.UUID, str],
        db: Session,
    ) -> Dict[str, Any]:
        """Verify the cryptographic integrity of the entire evidence log hash chain for a work order.

        Args:
            work_order_id: Unique identifier of target work order.
            db: SQLAlchemy database session.

        Returns:
            Dict[str, Any]: Verification status ('valid' or 'tampered'), verified block count, and violation details if any.
        """
        wo_uuid = self._resolve_uuid(work_order_id)
        blocks = (
            db.query(EvidenceLog)
            .filter(EvidenceLog.work_order_id == wo_uuid)
            .order_by(EvidenceLog.block_index.asc())
            .all()
        )

        if not blocks:
            return {
                "work_order_id": str(wo_uuid),
                "is_valid": True,
                "block_count": 0,
                "message": "No evidence log blocks found for this work order.",
            }

        expected_prev_hash = "0" * 64
        for idx, b in enumerate(blocks):
            # 1. Verify sequence
            if b.block_index != idx:
                return {
                    "work_order_id": str(wo_uuid),
                    "is_valid": False,
                    "block_count": len(blocks),
                    "tampered_block_index": b.block_index,
                    "error": f"Block index sequence mismatch: expected #{idx}, got #{b.block_index}",
                    "message": f"Cryptographic sequence violation detected at block #{b.block_index}.",
                }

            # 2. Verify previous hash pointer
            if b.previous_hash != expected_prev_hash:
                return {
                    "work_order_id": str(wo_uuid),
                    "is_valid": False,
                    "block_count": len(blocks),
                    "tampered_block_index": b.block_index,
                    "error": f"Previous hash pointer mismatch at block #{idx}: expected {expected_prev_hash}, got {b.previous_hash}",
                    "message": f"Broken cryptographic hash-chain pointer detected at block #{b.block_index}.",
                }

            # 3. Recompute and verify current hash
            canonical_json = json.dumps(b.payload, sort_keys=True)
            raw_block_str = f"{str(wo_uuid)}:{b.block_index}:{b.previous_hash}:{canonical_json}"
            recomputed_hash = hashlib.sha256(raw_block_str.encode("utf-8")).hexdigest()

            if recomputed_hash != b.current_hash:
                return {
                    "work_order_id": str(wo_uuid),
                    "is_valid": False,
                    "block_count": len(blocks),
                    "tampered_block_index": b.block_index,
                    "error": f"Cryptographic hash corruption at block #{idx}: stored {b.current_hash}, recomputed {recomputed_hash}",
                    "message": f"Data tampering detected in payload of block #{b.block_index}.",
                }

            expected_prev_hash = b.current_hash

        return {
            "work_order_id": str(wo_uuid),
            "is_valid": True,
            "block_count": len(blocks),
            "genesis_hash": blocks[0].current_hash,
            "head_hash": blocks[-1].current_hash,
            "tampered_block_index": None,
            "error": None,
            "message": f"Cryptographic integrity verified across all {len(blocks)} evidence blocks.",
        }


# Singleton accessor
_orchestrator_instance: Optional[OrchestratorModule] = None


def get_orchestrator_module() -> OrchestratorModule:
    """Provide singleton instance of OrchestratorModule."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorModule()
    return _orchestrator_instance
