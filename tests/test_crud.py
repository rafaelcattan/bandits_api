"""
Unit tests for CRUD operations.
"""
import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app import crud, models

# Use an in‑memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

def test_get_or_create_experiment(db_session):
    # Create a new experiment
    exp = crud.get_or_create_experiment(db_session, "test_exp")
    assert exp.id is not None
    assert exp.experiment_id == "test_exp"
    # Fetch the same experiment again
    exp2 = crud.get_or_create_experiment(db_session, "test_exp")
    assert exp2.id == exp.id
    # Different experiment
    exp3 = crud.get_or_create_experiment(db_session, "test_exp2")
    assert exp3.id != exp.id

def test_insert_daily_metrics(db_session):
    from app.schemas import VariantData
    # First create experiment
    exp = crud.get_or_create_experiment(db_session, "test_exp")
    variants = [
        VariantData(variant_id="control", impressions=1000, clicks=50),
        VariantData(variant_id="variant", impressions=1000, clicks=70)
    ]
    crud.insert_daily_metrics(db_session, "test_exp", date(2025, 12, 22), variants)
   
    # Verify that daily metrics were inserted
    metrics = db_session.query(models.DailyMetric).all()
    assert len(metrics) == 2
    metric_dict = {m.variant_name: (m.impressions, m.clicks) for m in metrics}
    assert metric_dict["control"] == (1000, 50)
    assert metric_dict["variant"] == (1000, 70)
    
    # Inserting the same data again should not create duplicates (due to unique constraint)
    crud.insert_daily_metrics(db_session, "test_exp", date(2025, 12, 22), variants)
    metrics = db_session.query(models.DailyMetric).all()
    assert len(metrics) == 2  # still two rows

def test_get_cumulative_metrics(db_session):
    from app.schemas import VariantData
    # Insert data for two days
    variants_day1 = [
        VariantData(variant_id="A", impressions=100, clicks=10),
        VariantData(variant_id="B", impressions=100, clicks=20)
    ]
    variants_day2 = [
        VariantData(variant_id="A", impressions=200, clicks=30),
        VariantData(variant_id="B", impressions=200, clicks=40)
    ]
    crud.insert_daily_metrics(db_session, "exp", date(2025, 12, 21), variants_day1)
    crud.insert_daily_metrics(db_session, "exp", date(2025, 12, 22), variants_day2)
    cumulative = crud.get_cumulative_metrics(db_session, "exp")
    assert set(cumulative.keys()) == {"A", "B"}
    assert cumulative["A"] == (40, 300)   # clicks: 10+30, impressions: 100+200
    assert cumulative["B"] == (60, 300)

def test_experiment_exists(db_session):
    assert not crud.experiment_exists(db_session, "nonexistent")
    crud.get_or_create_experiment(db_session, "new_exp")
    assert crud.experiment_exists(db_session, "new_exp")

if __name__ == "__main__":
    pytest.main([__file__])