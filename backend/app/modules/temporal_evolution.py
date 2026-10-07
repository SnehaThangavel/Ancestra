"""Module 5: Spatio-Temporal Deterioration Trend Forecasting and Rate Estimation.

SESCI Architecture - Module 5 (Temporal Evolution):
Analyzes sequential anomaly validation records to quantify deterioration velocity (dD/dt),
classifies regional degradation trajectory (increasing, decreasing, stable), and projects
future structural health indices with explicit uncertainty and confidence labeling.
Trend windows respect restoration boundary resets established in Module 3.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional, Union
from sqlalchemy.orm import Session

from app.models.consensus_state import ConsensusState
from app.models.validation import AnomalyValidation
from app.schemas.temporal import TemporalDataPoint
from app.utils.logging import get_logger

logger = get_logger(__name__)


class TemporalEvolutionModule:
    """Computes deterioration velocity (dD/dt) and projects structural health index over time horizons."""

    def __init__(self, critical_health_threshold: float = 0.40) -> None:
        """Initialize temporal evolution engine.

        Args:
            critical_health_threshold: Structural health index below which urgent intervention is triggered (default 0.40).
        """
        self.critical_health_threshold = critical_health_threshold

    @staticmethod
    def _resolve_uuid(val: Union[uuid.UUID, str, Any]) -> uuid.UUID:
        """Helper to cast ID into a standard UUID object."""
        if isinstance(val, uuid.UUID):
            return val
        return uuid.UUID(str(val))

    # -------------------------------------------------------------------------
    # 1. Deterioration Rate & Trajectory Estimation
    # -------------------------------------------------------------------------
    def estimate_deterioration_rate(
        self,
        region_id: Union[uuid.UUID, str],
        db: Session,
    ) -> Dict[str, Any]:
        """Estimate deterioration rate and classify trajectory for an architectural region.

        Requires 2+ AnomalyValidation records with anomaly_detected=True for that region.
        A restoration reset (Module 3 ConsensusState version bump) resets the trend window.

        Args:
            region_id: Unique UUID or string identifier for the architectural region.
            db: SQLAlchemy database session.

        Returns:
            Dict[str, Any]: Trend status, deterioration rate per day, trend classification,
                confidence assessment, and historical validation points.
        """
        region_uuid = self._resolve_uuid(region_id)

        # 1. Check for active consensus state to respect restoration reset boundaries
        active_consensus = (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == region_uuid)
            .order_by(ConsensusState.version.desc())
            .first()
        )

        query = db.query(AnomalyValidation).filter(
            AnomalyValidation.region_id == region_uuid,
            AnomalyValidation.severity_score >= 0.05,
        )

        # Reset trend window across restoration boundary (version > 1)
        if active_consensus and active_consensus.version > 1 and active_consensus.created_at:
            query = query.filter(AnomalyValidation.created_at >= active_consensus.created_at)

        validations = query.order_by(AnomalyValidation.created_at.asc()).all()

        if len(validations) < 2:
            return {
                "status": "insufficient_data",
                "region_id": str(region_uuid),
                "message": (
                    f"Insufficient validation records to compute deterioration rate. "
                    f"Found {len(validations)} detected anomalies; at least 2 are required within the current restoration window."
                ),
                "record_count": len(validations),
                "deterioration_rate_per_day": 0.0,
                "trend_classification": "stable",
                "projection_confidence": "low",
                "confidence_note": "Insufficient data (fewer than 2 anomaly validation records).",
                "historical_series": [
                    {
                        "timestamp": v.created_at.isoformat() if v.created_at else datetime.now(timezone.utc).isoformat(),
                        "severity_score": v.severity_score,
                        "anomaly_type": v.anomaly_type,
                    }
                    for v in validations
                ],
                "active_restoration_version": active_consensus.version if active_consensus else 1,
            }

        # 2. Extract timestamps and severity scores
        timestamps = [v.created_at for v in validations]
        severities = [float(v.severity_score) for v in validations]

        # Calculate time deltas in days from first point
        t0 = timestamps[0]
        days = [(t - t0).total_seconds() / 86400.0 for t in timestamps]
        span_days = max(0.0, days[-1] - days[0])
        record_count = len(validations)

        # 3. Compute rate of change (analytic OLS linear regression slope)
        if span_days > 1e-4:
            n = len(days)
            mean_x = sum(days) / float(n)
            mean_y = sum(severities) / float(n)
            numerator = sum((days[i] - mean_x) * (severities[i] - mean_y) for i in range(n))
            denominator = sum((days[i] - mean_x) ** 2 for i in range(n))

            if denominator > 1e-9:
                rate_per_day = float(numerator / denominator)
            else:
                rate_per_day = float((severities[-1] - severities[0]) / max(1e-4, span_days))
        else:
            # If all observations occurred at the exact same timestamp, compute delta directly
            delta_sev = severities[-1] - severities[0]
            rate_per_day = float(delta_sev)

        # 4. Classify trajectory as increasing, decreasing, or stable
        total_delta = severities[-1] - severities[0]
        if rate_per_day > 0.0005 or total_delta > 0.02:
            trend_classification = "increasing"
        elif rate_per_day < -0.0005 or total_delta < -0.02:
            trend_classification = "decreasing"
        else:
            trend_classification = "stable"

        # 5. Uncertainty & Confidence Assessment
        if record_count < 5 or span_days < 30.0:
            projection_confidence = "low"
            confidence_note = (
                f"Projection based on limited data ({record_count} records over {span_days:.1f} days) — "
                f"treat as a rough estimate, not a precise forecast."
            )
        elif record_count < 10 or span_days < 90.0:
            projection_confidence = "medium"
            confidence_note = (
                f"Projection based on moderate data ({record_count} records over {span_days:.1f} days) — "
                f"reasonable estimation with moderate uncertainty."
            )
        else:
            projection_confidence = "high"
            confidence_note = (
                f"High-confidence projection based on robust historical depth ({record_count} records over {span_days:.1f} days)."
            )

        return {
            "status": "calculated",
            "region_id": str(region_uuid),
            "deterioration_rate_per_day": round(rate_per_day, 6),
            "trend_classification": trend_classification,
            "projection_confidence": projection_confidence,
            "confidence_note": confidence_note,
            "record_count": record_count,
            "span_days": round(span_days, 2),
            "first_observed_at": timestamps[0].isoformat() if timestamps[0] else None,
            "last_observed_at": timestamps[-1].isoformat() if timestamps[-1] else None,
            "severity_start": severities[0],
            "severity_current": severities[-1],
            "total_severity_delta": round(total_delta, 4),
            "historical_series": [
                {
                    "timestamp": v.created_at.isoformat() if v.created_at else datetime.now(timezone.utc).isoformat(),
                    "severity_score": v.severity_score,
                    "ssim_delta": v.ssim_delta,
                    "anomaly_type": v.anomaly_type,
                    "is_confirmed": v.is_confirmed,
                }
                for v in validations
            ],
            "active_restoration_version": active_consensus.version if active_consensus else 1,
        }

    # -------------------------------------------------------------------------
    # 2. Future Structural Health Projection
    # -------------------------------------------------------------------------
    def project_future_health(
        self,
        region_id: Union[uuid.UUID, str],
        db: Session,
        horizon_days: int = 90,
        critical_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Linearly project structural health index over future horizons with confidence grading.

        Clearly labeled as an estimate based on recent anomaly validation history.

        Args:
            region_id: Unique UUID or string identifier for the architectural region.
            db: SQLAlchemy database session.
            horizon_days: Number of days forward to project (default 90 days).
            critical_threshold: Structural health index threshold for critical intervention (default 0.40).

        Returns:
            Dict[str, Any]: Current health, projected health, days to critical threshold, confidence, and estimate metadata.
        """
        region_uuid = self._resolve_uuid(region_id)
        crit_thresh = critical_threshold if critical_threshold is not None else self.critical_health_threshold

        # Fetch active ConsensusState
        active_consensus = (
            db.query(ConsensusState)
            .filter(ConsensusState.region_id == region_uuid)
            .order_by(ConsensusState.version.desc())
            .first()
        )

        current_health = (
            float(active_consensus.structural_health_index)
            if active_consensus and active_consensus.structural_health_index is not None
            else 1.0
        )

        trend_res = self.estimate_deterioration_rate(region_uuid, db=db)
        rate_per_day = trend_res.get("deterioration_rate_per_day", 0.0)

        # Health degradation rate is tied to severity rate: d(Health)/dt = - d(Severity)/dt
        # Projected health index bounded in [0.0, 1.0]
        projected_health = max(0.0, min(1.0, current_health - (rate_per_day * horizon_days)))

        # Time to critical threshold
        days_to_critical: Optional[float] = None
        if current_health <= crit_thresh:
            days_to_critical = 0.0
        elif rate_per_day > 1e-6:
            days_to_critical = max(0.0, (current_health - crit_thresh) / rate_per_day)

        return {
            "region_id": str(region_uuid),
            "is_projection_estimate": True,
            "projection_label": "Linear forecast estimate based on validated anomaly history",
            "projection_confidence": trend_res.get("projection_confidence", "low"),
            "confidence_note": trend_res.get("confidence_note"),
            "current_health_index": round(current_health, 4),
            "horizon_days": horizon_days,
            "projected_health_index": round(projected_health, 4),
            "deterioration_rate_per_day": rate_per_day,
            "trend_classification": trend_res.get("trend_classification", "stable"),
            "critical_threshold": crit_thresh,
            "time_to_critical_threshold_days": round(days_to_critical, 1) if days_to_critical is not None else None,
            "trend_status": trend_res.get("status"),
            "record_count": trend_res.get("record_count", 0),
            "span_days": trend_res.get("span_days", 0.0),
            "historical_series": trend_res.get("historical_series", []),
        }


# Singleton accessor
_temporal_instance: Optional[TemporalEvolutionModule] = None


def get_temporal_evolution() -> TemporalEvolutionModule:
    """Provide singleton instance of TemporalEvolutionModule."""
    global _temporal_instance
    if _temporal_instance is None:
        _temporal_instance = TemporalEvolutionModule()
    return _temporal_instance
