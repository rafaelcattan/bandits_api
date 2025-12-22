"""
CRUD operations for the Multi‑Armed Bandit database.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from typing import List, Tuple, Dict
import datetime

def get_or_create_experiment(db: Session, experiment_id: str) -> models.Experiment:
    """
    Retrieve an existing experiment by its external ID, or create a new one.
    """
    experiment = db.query(models.Experiment).filter(models.Experiment.experiment_id == experiment_id).first()
    if not experiment:
        experiment = models.Experiment(experiment_id=experiment_id)
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
    return experiment

def insert_daily_metrics(
    db: Session,
    experiment_id: str,
    date: datetime.date,
    variants: List[schemas.VariantData]
) -> None:
    """
    Insert daily metrics for all variants of an experiment.
    If a record for the same experiment/variant/date already exists, it will be skipped
    (due to unique constraint) or updated (if needed). This implementation skips duplicates.
    """
    experiment = get_or_create_experiment(db, experiment_id)
    for var in variants:
        # Check if a record already exists
        existing = db.query(models.DailyMetric).filter(
            models.DailyMetric.experiment_id == experiment.id,
            models.DailyMetric.variant_name == var.variant_id,
            models.DailyMetric.date == date
        ).first()
        if existing:
            # Update existing record (optional, could skip)
            existing.impressions = var.impressions
            existing.clicks = var.clicks
        else:
            metric = models.DailyMetric(
                experiment_id=experiment.id,
                variant_name=var.variant_id,
                date=date,
                impressions=var.impressions,
                clicks=var.clicks
            )
            db.add(metric)
    db.commit()

def get_cumulative_metrics(
    db: Session,
    experiment_id: str
) -> Dict[str, Tuple[int, int]]:
    """
    Retrieve cumulative clicks and impressions per variant for a given experiment.
    Returns a dictionary mapping variant_name -> (clicks, impressions).
    """
    result = db.query(
        models.DailyMetric.variant_name,
        func.sum(models.DailyMetric.clicks).label('total_clicks'),
        func.sum(models.DailyMetric.impressions).label('total_impressions')
    ).join(models.Experiment).filter(
        models.Experiment.experiment_id == experiment_id
    ).group_by(models.DailyMetric.variant_name).all()
    
    return {row.variant_name: (row.total_clicks or 0, row.total_impressions or 0) for row in result}

def experiment_exists(db: Session, experiment_id: str) -> bool:
    """Check if an experiment with given ID exists in the database."""
    return db.query(models.Experiment).filter(models.Experiment.experiment_id == experiment_id).first() is not None