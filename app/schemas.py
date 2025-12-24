"""
Pydantic schemas for request/response validation.
"""
from __future__ import annotations
from pydantic import BaseModel
from datetime import date
from typing import List

class VariantData(BaseModel):
    """Data for a single variant."""
    variant_id: str
    impressions: int
    clicks: int

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

class SuccessResponse(BaseModel):
    """Generic success response."""
    detail: str

class ErrorResponse(BaseModel):
    """Generic error response."""
    detail: str