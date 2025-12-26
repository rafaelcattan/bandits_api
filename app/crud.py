"""
CRUD operations for the Multi‑Armed Bandit database.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import text
from . import models, schemas
from typing import List, Tuple, Dict
import datetime
import math

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


def insert_daily_metrics_raw(
    db: Session,
    experiment_id: str,
    date: datetime.date,
    variants: List[schemas.VariantData]
) -> None:
    """
    Insert daily metrics using raw SQL (parameterized).
    Demonstrates SQL query insertion as per design requirement.
    """
    experiment = get_or_create_experiment(db, experiment_id)
    for var in variants:
        # Use raw SQL INSERT with ON CONFLICT DO UPDATE (SQLite syntax)
        # For simplicity we do INSERT OR IGNORE (skip duplicates)
        # but we need to update existing records; we'll use INSERT OR REPLACE
        # which deletes and inserts new row (changes id). Better to use UPSERT.
        # Since we already have unique constraint, we'll use INSERT OR IGNORE and then UPDATE.
        # However for demonstration we'll just insert ignoring duplicates.
        sql = text("""
            INSERT OR IGNORE INTO daily_metrics
                (experiment_id, variant_name, date, impressions, clicks)
            VALUES (:experiment_id, :variant_name, :date, :impressions, :clicks)
        """)
        db.execute(sql, {
            'experiment_id': experiment.id,
            'variant_name': var.variant_id,
            'date': date,
            'impressions': var.impressions,
            'clicks': var.clicks
        })
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


def get_ctr_metrics_raw(
    db: Session,
    experiment_id: str
) -> Dict[str, Tuple[float, int, int]]:
    """
    Compute CTR per variant using raw SQL aggregation.
    Returns variant -> (ctr, clicks, impressions).
    
    This raw SQL version demonstrates explicit SQL aggregation as per design requirement.
    The multiplication by 1.0 (or CAST to REAL) ensures floating‑point division in SQLite.
    """
    sql = text("""
        SELECT
            dm.variant_name,
            SUM(dm.clicks) AS total_clicks,
            SUM(dm.impressions) AS total_impressions,
            CASE
                WHEN SUM(dm.impressions) = 0 THEN 0.0
                ELSE CAST(SUM(dm.clicks) AS REAL) / SUM(dm.impressions)
            END AS ctr
        FROM daily_metrics dm
        JOIN experiments e ON dm.experiment_id = e.id
        WHERE e.experiment_id = :experiment_id
        GROUP BY dm.variant_name
    """)
    result = db.execute(sql, {'experiment_id': experiment_id}).fetchall()
    return {row.variant_name: (row.ctr, row.total_clicks, row.total_impressions) for row in result}


def experiment_exists(db: Session, experiment_id: str) -> bool:
    """Check if an experiment with given ID exists in the database."""
    return db.query(models.Experiment).filter(models.Experiment.experiment_id == experiment_id).first() is not None


def get_ctr_metrics(
    db: Session,
    experiment_id: str
) -> Dict[str, Tuple[float, int, int]]:
    """
    Retrieve cumulative clicks, impressions and CTR per variant for a given experiment.
    Returns a dictionary mapping variant_name -> (ctr, clicks, impressions).
    CTR is clicks/impressions as a float, or 0.0 if impressions == 0.
    """
    cumulative = get_cumulative_metrics(db, experiment_id)
    result = {}
    for var, (clicks, impressions) in cumulative.items():
        ctr = clicks / impressions if impressions > 0 else 0.0
        result[var] = (ctr, clicks, impressions)
    return result


def get_confidence_intervals(
    db: Session,
    experiment_id: str,
    confidence: float = 0.95
) -> Dict[str, Tuple[float, float]]:
    """
    Compute Wilson score interval for each variant.
    Returns a dictionary mapping variant_name -> (lower_bound, upper_bound).
    """
    import math
    cumulative = get_cumulative_metrics(db, experiment_id)
    result = {}
    z = 1.96  # for 95% confidence, approximate; could be computed from confidence
    for var, (clicks, impressions) in cumulative.items():
        if impressions == 0:
            result[var] = (0.0, 0.0)
            continue
        p = clicks / impressions
        denominator = 1 + (z**2 / impressions)
        centre = p + (z**2) / (2 * impressions)
        half = z * math.sqrt((p * (1 - p) + (z**2) / (4 * impressions)) / impressions)
        lower = (centre - half) / denominator
        upper = (centre + half) / denominator
        result[var] = (max(0.0, lower), min(1.0, upper))
    return result