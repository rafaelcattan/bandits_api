"""
Multi‑Armed Bandit algorithms for traffic allocation.
"""
import random
from typing import Dict, List, Tuple
import math

def thompson_sampling_allocation(
    cumulative_metrics: Dict[str, Tuple[int, int]],
    num_samples: int = 10000
) -> Dict[str, float]:
    """
    Compute allocation percentages using Thompson Sampling (Beta‑Binomial).
    
    Args:
        cumulative_metrics: mapping variant_name -> (clicks, impressions)
        num_samples: number of Monte Carlo samples (default 10,000)
    
    Returns:
        mapping variant_name -> percentage (0‑100)
    """
    if not cumulative_metrics:
        raise ValueError("cumulative_metrics cannot be empty")
    
    variants = list(cumulative_metrics.keys())
    # Compute posterior Beta parameters
    alpha = []
    beta = []
    for var in variants:
        clicks, impressions = cumulative_metrics[var]
        # Prior Beta(1,1)
        a = 1 + clicks
        b = 1 + impressions - clicks
        alpha.append(a)
        beta.append(b)
    
    # Monte Carlo sampling
    wins = {var: 0 for var in variants}
    for _ in range(num_samples):
        samples = []
        for a, b in zip(alpha, beta):
            # Draw from Beta distribution
            samples.append(random.betavariate(a, b))
        # Find variant with highest sample
        best_idx = samples.index(max(samples))
        wins[variants[best_idx]] += 1
    
    # Convert to percentages
    total = num_samples
    percentages = {var: (wins[var] / total) * 100.0 for var in variants}
    return percentages

def allocation_to_sorted_list(percentages: Dict[str, float]) -> List[Tuple[str, float]]:
    """Convert percentages dictionary to a list sorted by percentage descending."""
    return sorted(percentages.items(), key=lambda x: x[1], reverse=True)