"""
SQLAlchemy models for the Multi‑Armed Bandit database.
Hybrid schema: experiments + daily_metrics tables.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
class Experiment(Base):
    """Experiments table. """
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    daily_metrics = relationship("DailyMetric", back_populates="experiment", cascade="all, delete-orphan")

class DailyMetric(Base):
    """Daily metrics for each variant of an experiment."""
    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    variant_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    impressions = Column(Integer, nullable=False)
    clicks = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    experiment = relationship("Experiment", back_populates="daily_metrics")

    # Composite unique constraint to avoid duplicate entries for same experiment/variant/date
    __table_args__ = (
        UniqueConstraint('experiment_id', 'variant_name', 'date', name='uix_experiment_variant_date'),
    )