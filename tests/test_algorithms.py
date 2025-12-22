"""
Unit tests for the Multi‑Armed Bandit algorithms.
"""
import pytest
from app.algorithms import thompson_sampling_allocation

def test_thompson_sampling_allocation_basic():
    # Simple case: two variants with equal performance
    cumulative = {
        "control": (50, 1000),   # 5% CTR
        "variant": (50, 1000)    # 5% CTR
    }
    result = thompson_sampling_allocation(cumulative, num_samples=5000)
    assert set(result.keys()) == {"control", "variant"}
    # Percentages should be roughly equal (allow some randomness)
    assert 40 < result["control"] < 60
    assert 40 < result["variant"] < 60
    assert abs(result["control"] + result["variant"] - 100.0) < 0.01

def test_thompson_sampling_allocation_skewed():
    # Variant A performs better
    cumulative = {
        "A": (100, 1000),   # 10% CTR
        "B": (10, 1000)     # 1% CTR
    }
    result = thompson_sampling_allocation(cumulative, num_samples=5000)
    assert result["A"] > result["B"]
    # A should get majority of traffic
    assert result["A"] > 70
    assert result["B"] < 30

def test_thompson_sampling_allocation_three_variants():
    cumulative = {
        "low": (5, 100),
        "medium": (20, 100),
        "high": (50, 100)
    }
    result = thompson_sampling_allocation(cumulative, num_samples=5000)
    assert len(result) == 3
    # Order should be high >= medium >= low (allow equality due to randomness)
    assert result["high"] >= result["medium"]
    assert result["medium"] >= result["low"]
    assert abs(sum(result.values()) - 100.0) < 0.01

def test_thompson_sampling_allocation_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        thompson_sampling_allocation({})

def test_thompson_sampling_allocation_zero_impressions():
    # Edge case: zero impressions (clicks must be zero)
    cumulative = {
        "A": (0, 0),
        "B": (0, 0)
    }
    result = thompson_sampling_allocation(cumulative, num_samples=1000)
    # With no data, prior Beta(1,1) leads to equal allocation
    assert abs(result["A"] - 50.0) < 5  # allow random variation
    assert abs(result["B"] - 50.0) < 5

if __name__ == "__main__":
    pytest.main([__file__])