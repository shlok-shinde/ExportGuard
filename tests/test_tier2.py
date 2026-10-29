"""
Unit tests for Tier 2: Stream Sampling & Fingerprinting.
"""
import os
import pytest
from backend.analyzers.tier2_sampling import run_tier2

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

def test_valid_export_tier2():
    gz = os.path.join(FIXTURES, 'valid_export.gz')
    res = run_tier2(gz, target_sample_fraction=0.01)
    
    assert res['passed'] is True
    # 100k data rows + 1 sentinel row = 100,001 rows
    assert res['streaming_row_count'] == 100001
    assert len(res['header_fingerprint']) == 64  # SHA-256
    assert res['boundary_validation']['last_row_matches_header_width'] is True
    assert len(res['column_profiles']) == 6
    assert res['calculated_xor_checksum'].startswith('0x')

def test_high_compression_export_row_count():
    gz = os.path.join(FIXTURES, 'high_compression_export.gz')
    res = run_tier2(gz, target_sample_fraction=0.01)
    
    assert res['passed'] is True
    # 130k data rows + 1 sentinel row = 130,001 rows (+30% rows verified)
    assert res['streaming_row_count'] == 130001
    assert res['boundary_validation']['header_column_count'] == 6
    assert res['boundary_validation']['last_row_matches_header_width'] is True

def test_pipe_truncated_export_row_shortfall():
    gz = os.path.join(FIXTURES, 'pipe_truncated_export.gz')
    res = run_tier2(gz, target_sample_fraction=0.01)
    
    # Exactly 70,000 rows found instead of 100,000!
    assert res['streaming_row_count'] == 70000
