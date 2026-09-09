"""Conservation work orders and cryptographic hash-chained evidence logs."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class WorkOrder(Base):
    """Conservation intervention work order model."""

    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(
            "urgency_index >= 0.0 AND urgency_index <= 1.0",
            name="check_urgency_index",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    validation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("anomaly_validations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    urgency_index = Column(Float, nullable=False)  # composite urgency metric [0.0, 1.0]
    status = Column(String(32), default="pending", nullable=False)  # pending, assigned, in_progress, completed
    assigned_team = Column(String(128), nullable=True)
    recommended_action = Column(String(256), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    validation = relationship("AnomalyValidation", back_populates="work_orders")
    evidence_logs = relationship("EvidenceLog", back_populates="work_order", cascade="all, delete-orphan")

    # Compatibility properties
    @property
    def urgency_score(self):
        return self.urgency_index

    @urgency_score.setter
    def urgency_score(self, value):
        self.urgency_index = value


class EvidenceLog(Base):
    """Immutable hash-chained evidence log entry for auditing conservation findings."""

    __tablename__ = "evidence_logs"
    __table_args__ = (
        UniqueConstraint("work_order_id", "block_index", name="uq_evidence_logs_work_order_block"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("work_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_index = Column(Integer, nullable=False)
    previous_hash = Column(String(64), nullable=False)  # SHA-256 hash of prior block
    current_hash = Column(String(64), nullable=False)   # SHA-256 hash of this entry
    payload = Column(JSONB, nullable=False)             # immutable snapshot data
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    work_order = relationship("WorkOrder", back_populates="evidence_logs")

    # Compatibility properties
    @property
    def payload_snapshot(self):
        return self.payload

    @payload_snapshot.setter
    def payload_snapshot(self, value):
        self.payload = value

    @property
    def timestamp(self):
        return self.created_at

    @timestamp.setter
    def timestamp(self, value):
        self.created_at = value
