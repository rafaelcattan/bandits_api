"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import List

class VariantData(BaseModel):
    """Data for a single variant."""
    variant_id: str = Field(..., description="Variant identifier (e.g., 'control', 'variant')")
    impressions: int = Field(..., ge=0, description="Number of impressions (exposures)")
    clicks: int = Field(..., ge=0, description="Number of clicks (successes)")

class ExperimentData(BaseModel):
    """Request schema for POST /data."""
    experiment_id: str = Field(..., description="Unique experiment identifier")
    date: date = Field(..., description="Date of the recorded metrics (YYYY-MM-DD)")
    variants: List[VariantData] = Field(..., min_length=2, description="List of variant data")

class AllocationVariant(BaseModel):
    """Allocation for a single variant."""
    variant_id: str = Field(..., description="Variant identifier")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Recommended traffic percentage")

class AllocationResponse(BaseModel):
    """Response schema for GET /allocation."""
    experiment_id: str = Field(..., description="Experiment identifier")
    date: date = Field(..., description="Date for which allocation is recommended")
    allocations: List[AllocationVariant] = Field(..., description="Allocation percentages per variant")

class SuccessResponse(BaseModel):
    """Generic success response."""
    detail: str = Field(..., description="Success message")

class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str = Field(..., description="Error description")