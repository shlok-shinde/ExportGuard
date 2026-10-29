#!/usr/bin/env bash
# ==============================================================================
# ExportGuard CLI Tool
# High-speed Zero-Footprint Compressed Database Export Verification
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_export.gz> [optional_log_file.log] [prev_rows] [curr_rows] [prev_size_bytes]"
    echo "Example: $0 tests/fixtures/high_compression_export.gz tests/fixtures/valid_expdp.log 100000 130000 2004185"
    exit 1
fi

EXPORT_FILE="$1"
LOG_FILE="${2:-}"
PREV_ROWS="${3:-100000}"
CURR_ROWS="${4:-130000}"
PREV_SIZE="${5:-2000000}"

echo "===================================================================="
echo " 🔒 EXPORTGUARD FORENSIC AUDIT PIPELINE"
echo " Target Export: ${EXPORT_FILE}"
echo "===================================================================="

source "${PROJECT_ROOT}/.venv/bin/activate"

python3 - <<EOF
import sys
import json
from backend.analyzers.tier1_envelope import run_tier1
from backend.analyzers.tier2_sampling import run_tier2
from backend.analyzers.tier3_forensic import run_tier3
from backend.analyzers.report_generator import generate_full_report

gz_path = "${EXPORT_FILE}"
log_path = "${LOG_FILE}" if "${LOG_FILE}" else None
prev_rows = int("${PREV_ROWS}")
curr_rows = int("${CURR_ROWS}")
prev_size = int("${PREV_SIZE}")

print("[Phase 1/3] Executing Tier 1 Envelope Checks...")
t1 = run_tier1(gz_path, log_path, prev_size_bytes=prev_size, curr_rows=curr_rows, prev_rows=prev_rows)

t2 = None
t3 = None
if t1['gzip_container']['gzip_t_passed']:
    print("[Phase 2/3] Executing Tier 2 Stream Sampling...")
    t2 = run_tier2(gz_path)
    print("[Phase 3/3] Executing Tier 3 Deep Forensics...")
    t3 = run_tier3(gz_path)

report = generate_full_report(gz_path, t1, t2, t3)

print("\n" + "=" * 68)
print(f" FINAL VERDICT: {report['verdict']} ({report['verdict_severity']})")
print(f" Summary:       {report['verdict_summary']}")
print("=" * 68)
print(f"\nRoot Cause & Explanation:\n{report['root_cause_explanation']}\n")

if report['tier1']['sentinel_check']['passed']:
    print(" [✓] Stream Completion Sentinel: VERIFIED")
else:
    print(" [✗] Stream Completion Sentinel: MISSING / TRUNCATED")

if report['tier1']['gzip_container']['gzip_t_passed']:
    print(f" [✓] GZIP Container CRC-32:     VALID ({report['tier1']['gzip_container']['stored_crc32']})")
else:
    print(f" [✗] GZIP Container CRC-32:     CORRUPT ({report['tier1']['gzip_container']['gzip_t_error']})")

if t2:
    print(f" [✓] Stream Row Count:          {t2['streaming_row_count']:,} rows")
    print(f" [✓] Schema SHA-256:            {t2['header_fingerprint'][:24]}...")
    print(f" [✓] Commutative XOR Checksum:  {t2['calculated_xor_checksum']}")

if t3:
    print(f" [✓] Average Shannon Entropy:   {t3['entropy_analysis']['average_entropy']} bits/byte")
    print(f" [✓] 64KB Merkle Root:          {t3['block_merkle_verification']['merkle_root'][:24]}...")

sys.exit(0 if report['verdict'] == 'INTACT' else 1)
EOF
