"""
Unit tests for Tier 1: Envelope Checks.
Verifies container inspection, sentinel detection, and anomaly scoring.
"""
import os
import pytest
from backend.analyzers.tier1_envelope import run_tier1
from backend.utils.sentinels import check_sentinel

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

def test_valid_export_tier1():
    gz = os.path.join(FIXTURES, 'valid_export.gz')
    log = os.path.join(FIXTURES, 'valid_expdp.log')
    res = run_tier1(gz, log)
    assert res['passed'] is True
    assert res['sentinel_check']['passed'] is True
    assert res['gzip_container']['gzip_t_passed'] is True
    assert res['log_parser']['completed_cleanly'] is True

def test_pipe_truncated_export_fails_sentinel_despite_gzip_t_passing():
    """
    CRITICAL RESEARCH VERIFICATION:
    gzip -t returns True, but sentinel check MUST return False.
    """
    gz = os.path.join(FIXTURES, 'pipe_truncated_export.gz')
    res = run_tier1(gz)
    
    # gzip container is syntactically pristine
    assert res['gzip_container']['gzip_t_passed'] is True
    # BUT sentinel check fails
    assert res['sentinel_check']['passed'] is False
    assert res['sentinel_check']['severity'] == 'CRITICAL'
    # Tier 1 overall MUST fail
    assert res['passed'] is False

def test_raw_truncated_export_fails_container():
    gz = os.path.join(FIXTURES, 'truncated_export.gz')
    res = run_tier1(gz)
    assert res['gzip_container']['gzip_t_passed'] is False
    assert res['passed'] is False

def test_corrupted_export_fails_crc():
    gz = os.path.join(FIXTURES, 'corrupted_export.gz')
    res = run_tier1(gz)
    assert res['gzip_container']['gzip_t_passed'] is False
    assert res['passed'] is False

def test_high_compression_export_passes_with_entropy_explanation():
    gz = os.path.join(FIXTURES, 'high_compression_export.gz')
    res = run_tier1(gz, curr_rows=130000, prev_rows=100000, prev_size_bytes=2004185)
    assert res['passed'] is True
    assert res['anomaly_scorer']['verdict'] == 'PLAUSIBLE_ENTROPY_DROP'
    assert 'LZ77' in res['anomaly_scorer']['explanation']

def test_oracle_log_with_ora1555_detected():
    gz = os.path.join(FIXTURES, 'valid_export.gz')
    log = os.path.join(FIXTURES, 'corrupt_ora1555.log')
    res = run_tier1(gz, log)
    assert res['passed'] is False
    assert any(e['code'] == 'ORA-01555' for e in res['log_parser']['errors_found'])
