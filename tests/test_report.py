"""
End-to-End integration test for full report generation across all 5 fixture scenarios.
"""
import os
from backend.analyzers.tier1_envelope import run_tier1
from backend.analyzers.tier2_sampling import run_tier2
from backend.analyzers.tier3_forensic import run_tier3
from backend.analyzers.report_generator import generate_full_report

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

def test_e2e_valid_export():
    gz = os.path.join(FIXTURES, 'valid_export.gz')
    log = os.path.join(FIXTURES, 'valid_expdp.log')
    t1 = run_tier1(gz, log)
    t2 = run_tier2(gz)
    t3 = run_tier3(gz)
    report = generate_full_report('valid_export.gz', t1, t2, t3)
    assert report['verdict'] == 'INTACT'
    assert report['verdict_severity'] == 'SUCCESS'

def test_e2e_pipe_truncated_export():
    """SHOWSTOPPER: Verified as CORRUPTED due to pipe termination."""
    gz = os.path.join(FIXTURES, 'pipe_truncated_export.gz')
    t1 = run_tier1(gz)
    report = generate_full_report('pipe_truncated_export.gz', t1)
    assert report['verdict'] == 'CORRUPTED'
    assert report['verdict_severity'] == 'CRITICAL'
    assert 'Pipe Truncation' in report['verdict_summary']

def test_e2e_high_compression_export():
    """Innocent scenario: Verified as INTACT with mathematical explanation."""
    gz = os.path.join(FIXTURES, 'high_compression_export.gz')
    t1 = run_tier1(gz, curr_rows=130000, prev_rows=100000, prev_size_bytes=2004185)
    t2 = run_tier2(gz)
    t3 = run_tier3(gz)
    report = generate_full_report('high_compression_export.gz', t1, t2, t3)
    assert report['verdict'] == 'INTACT'
    assert report['verdict_severity'] == 'SUCCESS'
    assert 'Repetitive Data Compression' in report['verdict_summary']

def test_e2e_corrupted_export():
    gz = os.path.join(FIXTURES, 'corrupted_export.gz')
    t1 = run_tier1(gz)
    report = generate_full_report('corrupted_export.gz', t1)
    assert report['verdict'] == 'CORRUPTED'
    assert report['verdict_severity'] == 'CRITICAL'
