"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from pydantic import BaseModel, field_validator, model_validator
from datetime import date
from typing import List, Optional

class VariantData(BaseModel):
    """Data for a single variant."""
    variant_id: str
    impressions: int
    clicks: int

    @model_validator(mode='after')
    def validate_clicks_impressions(self):
        if self.clicks > self.impressions:
            raise ValueError('clicks cannot exceed impressions')
        return self

class ExperimentData(BaseModel):
    """Request schema for POST /data."""
    experiment_id: str
    date: date
    variants: List[VariantData]

class AllocationVariant(BaseModel):
    """Allocation for a single variant."""
    variant_id: str
    percentage: float

class AllocationResponse(BaseModel):
    """Response schema for GET /allocation."""
    experiment_id: str
    date: date
    allocations: List[AllocationVariant]


class VariantMetrics(BaseModel):
    """Metrics for a single variant."""
    variant_id: str
    clicks: int
    impressions: int
    ctr: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class MetricsResponse(BaseModel):
    """Response schema for GET /metrics."""
    experiment_id: str
    date: date
    variants: List[VariantMetrics]


class SuccessResponse(BaseModel):
    """Generic success response."""
    detail: str

class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str