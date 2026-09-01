"""Conservation work orders and cryptographic hash-chained evidence logs."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class WorkOrder(Base):
    """Conservation intervention work order model."""

    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(Integer, ForeignKey("anomaly_validations.id"), nullable=False)
    urgency_score = Column(Float, nullable=False)  # composite urgency metric
    status = Column(String(32), default="pending", nullable=False)  # pending, assigned, in_progress, completed
    assigned_team = Column(String(128), nullable=True)
    recommended_action = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    validation = relationship("AnomalyValidation", back_populates="work_orders")
    evidence_logs = relationship("EvidenceLog", back_populates="work_order")


class EvidenceLog(Base):
    """Immutable hash-chained evidence log entry for auditing conservation findings."""

    __tablename__ = "evidence_logs"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(Integer, ForeignKey("work_orders.id"), nullable=False)
    previous_hash = Column(String(64), nullable=False)  # SHA-256 hash of prior block
    current_hash = Column(String(64), nullable=False)   # SHA-256 hash of this entry
    payload_snapshot = Column(JSON, nullable=False)      # immutable snapshot data
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    work_order = relationship("WorkOrder", back_populates="evidence_logs")
