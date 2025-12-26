"""
FastAPI application for Multi‑Armed Bandit Optimization API.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
import logging

from . import crud, schemas, algorithms
from .database import get_db, create_tables

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Multi‑Armed Bandit Optimization API",
    description="API that receives temporal data from Multi‑Armed Bandit experiments, processes it using SQL, and returns optimal traffic allocation percentages.",
    version="1.0.0"
)

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    logger.info("Database tables created (if not exist).")

@app.get("/")
def root():
    return {
        "message": "Multi‑Armed Bandit Optimization API",
        "docs": "/docs",
        "endpoints": {
            "POST /data": "Submit daily experiment metrics",
            "GET /allocation": "Get allocation percentages for the next day",
            "GET /metrics": "Get experiment metrics (CTR, confidence intervals)"
        }
    }

@app.post("/data", response_model=schemas.SuccessResponse, status_code=200)
def post_data(
    data: schemas.ExperimentData,
    db: Session = Depends(get_db)
):
    """
    Receive daily metrics for a Multi‑Armed Bandit experiment.
    
    - **experiment_id**: unique identifier for the experiment
    - **date**: date of the recorded metrics (YYYY‑MM‑DD)
    - **variants**: list of variant data (impressions and clicks)
    
    The data will be stored in the SQL database for later analysis.
    """
    try:
        crud.insert_daily_metrics(db, data.experiment_id, data.date, data.variants)
        logger.info(f"Data stored for experiment {data.experiment_id} on {data.date}")
        return {"detail": "Data stored successfully"}
    except Exception as e:
        logger.error(f"Failed to store data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/allocation", response_model=schemas.AllocationResponse)
def get_allocation(
    experiment_id: str = Query(..., description="Experiment identifier"),
    target_date: date = Query(None, description="Date for which allocation is requested (defaults to tomorrow)"),
    db: Session = Depends(get_db)
):
    """
    Return recommended traffic allocation percentages for the next day.
    
    The allocation is computed using Thompson Sampling over all historical data
    for the given experiment.
    
    - **experiment_id**: required query parameter
    - **target_date**: optional; if omitted, defaults to tomorrow (UTC date)
    """
    # Determine target date
    if target_date is None:
        target_date = date.today() + timedelta(days=1)
    
    # Check if experiment exists and has data
    if not crud.experiment_exists(db, experiment_id):
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    
    # Retrieve cumulative metrics
    cumulative = crud.get_cumulative_metrics(db, experiment_id)
    if not cumulative:
        raise HTTPException(status_code=404, detail=f"No data available for experiment '{experiment_id}'")
    
    # Compute allocation using Thompson Sampling
    try:
        percentages = algorithms.thompson_sampling_allocation(cumulative)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Build response
    allocations = [
        schemas.AllocationVariant(variant_id=var, percentage=round(pct, 2))
        for var, pct in percentages.items()
    ]
    
    return schemas.AllocationResponse(
        experiment_id=experiment_id,
        date=target_date,
        allocations=allocations
    )


@app.get("/metrics", response_model=schemas.MetricsResponse)
def get_metrics(
    experiment_id: str = Query(..., description="Experiment identifier"),
    include_confidence: bool = Query(False, description="Include confidence intervals (Wilson score)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve cumulative metrics (clicks, impressions, CTR) for each variant.
    Optionally include Wilson score confidence intervals.
    """
    # Check if experiment exists
    if not crud.experiment_exists(db, experiment_id):
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found")
    
    # Get CTR metrics
    ctr_metrics = crud.get_ctr_metrics(db, experiment_id)
    if not ctr_metrics:
        raise HTTPException(status_code=404, detail=f"No data available for experiment '{experiment_id}'")
    
    # Get confidence intervals if requested
    confidence_intervals = None
    if include_confidence:
        confidence_intervals = crud.get_confidence_intervals(db, experiment_id)
    
    # Build variant metrics list
    variants = []
    for var, (ctr, clicks, impressions) in ctr_metrics.items():
        lower = upper = None
        if include_confidence and confidence_intervals and var in confidence_intervals:
            lower, upper = confidence_intervals[var]
        variants.append(
            schemas.VariantMetrics(
                variant_id=var,
                clicks=clicks,
                impressions=impressions,
                ctr=round(ctr, 4),
                lower_bound=round(lower, 4) if lower is not None else None,
                upper_bound=round(upper, 4) if upper is not None else None
            )
        )
    
    return schemas.MetricsResponse(
        experiment_id=experiment_id,
        date=date.today(),
        variants=variants
    )


@app.get("/health")
def health_check():
    """Simple health endpoint."""
    return {"status": "healthy"}