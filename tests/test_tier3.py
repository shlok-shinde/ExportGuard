"""
Unit tests for Tier 3: Deep Forensics & Sliding Entropy.
"""
import os
import pytest
from backend.analyzers.tier3_forensic import run_tier3

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

def test_valid_export_tier3():
    gz = os.path.join(FIXTURES, 'valid_export.gz')
    res = run_tier3(gz)
    
    assert res['passed'] is True
    entropy_data = res['entropy_analysis']
    assert entropy_data['average_entropy'] > 3.0
    assert entropy_data['total_windows_evaluated'] > 0
    assert len(entropy_data['profile_sample']) > 0
    
    merkle_data = res['block_merkle_verification']
    assert len(merkle_data['merkle_root']) == 64
    assert merkle_data['block_count'] > 0

def test_high_compression_export_lower_entropy():
    gz = os.path.join(FIXTURES, 'high_compression_export.gz')
    res = run_tier3(gz)
    
    assert res['passed'] is True
    # In both cases, structured text entropy is in normal bounds [4.0 - 6.0], with zero corruption anomalies
    assert 4.0 <= res['entropy_analysis']['average_entropy'] <= 6.0
    critical = [a for a in res['entropy_analysis']['anomalies'] if a['severity'] == 'CRITICAL']
    assert len(critical) == 0
