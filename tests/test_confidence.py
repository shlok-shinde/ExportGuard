"""
Unit tests for statistical confidence calculations.
"""
from backend.utils.confidence import compute_sampling_confidence

def test_confidence_cochran_minimum():
    """Formula: ln(0.05) / ln(0.95) ≈ 59 rows to detect 5% corruption with 95% confidence."""
    res = compute_sampling_confidence(population_size=10000000, sample_size=1000)
    assert res['min_sample_for_95pct_conf_at_5pct_corruption'] == 59

def test_rule_of_three():
    """Rule of Three: with 0 defects in 30,000 samples, upper bound defect rate <= 0.01%."""
    res = compute_sampling_confidence(population_size=1000000, sample_size=30000, defects_found=0)
    rot = res['rule_of_three']
    assert rot is not None
    assert rot['upper_bound_corruption_rate_pct'] <= 0.01
    assert rot['max_possible_corrupted_rows'] <= 100
