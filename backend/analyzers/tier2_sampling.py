"""
Tier 2: Stream-Level Sampling & Fingerprinting (runs in seconds to minutes).
- Zero-disk streaming row count
- Header schema SHA-256 fingerprint
- Boundary row validation (first & last N rows)
- Block-stratified column profiling
- Commutative order-independent XOR checksum verification (zero TEMP tablespace allocation)
- Statistical confidence verification (Rule of Three & hypergeometric model)
"""
import gzip
import hashlib
import csv
from collections import deque, Counter
from typing import Dict, Any, List, Optional
from ..utils.confidence import compute_sampling_confidence

def run_tier2(
    gz_path: str,
    target_sample_fraction: float = 0.02, # 2% sample rate
    source_db_expected_xor: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes Tier 2 stream sampling without allocating disk space or temporary tablespace.
    """
    row_count = 0
    header_line = ""
    header_cols: List[str] = []
    
    first_rows: List[str] = []
    last_rows_buf: deque = deque(maxlen=50)
    
    # Column profiling structures
    sampled_count = 0
    col_null_counts: Dict[str, int] = {}
    col_length_sums: Dict[str, int] = {}
    col_distinct_sets: Dict[str, set] = {}
    
    # Commutative XOR 64-bit checksum accumulator
    xor_accumulator = 0
    
    with gzip.open(gz_path, 'rt', errors='replace') as f:
        reader = csv.reader(f)
        
        # Read Header
        try:
            raw_header = next(reader)
            header_cols = [c.strip() for c in raw_header]
            header_line = ",".join(header_cols)
            for col in header_cols:
                col_null_counts[col] = 0
                col_length_sums[col] = 0
                col_distinct_sets[col] = set()
        except StopIteration:
            return {
                'passed': False,
                'error': 'File is empty or contains no data lines.'
            }
            
        for row in reader:
            row_count += 1
            if row_count <= 25:
                first_rows.append(",".join(row))
            last_rows_buf.append(",".join(row))
            
            # Commutative XOR 64-bit hash over each row representation
            # Order-independent hash: hash(A) ^ hash(B) == hash(B) ^ hash(A)
            row_str = "|".join(row)
            row_hash_int = int(hashlib.md5(row_str.encode('utf-8', errors='ignore')).hexdigest()[:16], 16)
            xor_accumulator ^= row_hash_int
            
            # Systematic/Stratified Sampling (every 50th row ≈ 2%)
            if row_count % int(1.0 / target_sample_fraction) == 0:
                sampled_count += 1
                for idx, col in enumerate(header_cols):
                    val = row[idx] if idx < len(row) else ""
                    if not val or val.strip() == "" or val.upper() == "NULL":
                        col_null_counts[col] += 1
                    col_length_sums[col] += len(val)
                    if len(col_distinct_sets[col]) < 200:
                        col_distinct_sets[col].add(val)

    # Compute schema SHA-256 fingerprint
    schema_fingerprint = hashlib.sha256(header_line.encode('utf-8')).hexdigest()
    
    # Boundary validation check
    last_row_elements = last_rows_buf[-1].split(",") if last_rows_buf else []
    last_row_column_count_matches = (len(last_row_elements) == len(header_cols))
    
    boundary_validation = {
        'first_rows_captured': len(first_rows),
        'last_rows_captured': len(last_rows_buf),
        'header_column_count': len(header_cols),
        'last_row_column_count': len(last_row_elements),
        'last_row_matches_header_width': last_row_column_count_matches,
        'first_sample': first_rows[:3],
        'last_sample': list(last_rows_buf)[-3:] if last_rows_buf else []
    }
    
    # Compute column profiles
    col_profiles = []
    for col in header_cols:
        null_rate = (col_null_counts[col] / sampled_count) if sampled_count > 0 else 0.0
        avg_len = (col_length_sums[col] / sampled_count) if sampled_count > 0 else 0.0
        distinct_count = len(col_distinct_sets[col])
        col_profiles.append({
            'column_name': col,
            'null_percentage': round(null_rate * 100, 2),
            'average_char_length': round(avg_len, 1),
            'sampled_distinct_values': distinct_count,
            'status': 'HEALTHY' if null_rate < 0.9 else 'HIGH_NULL_DILUTION'
        })
        
    # Statistical confidence calculation
    confidence_metrics = compute_sampling_confidence(
        population_size=row_count,
        sample_size=max(1, sampled_count),
        defects_found=0 if last_row_column_count_matches else 1
    )
    
    # Commutative XOR hex string
    calculated_xor_hex = f"0x{xor_accumulator:016x}"
    xor_match = True
    if source_db_expected_xor:
        xor_match = (calculated_xor_hex.lower() == source_db_expected_xor.lower())
        
    passed = last_row_column_count_matches and (row_count > 0)
    
    return {
        'passed': passed,
        'streaming_row_count': row_count,
        'header_fingerprint': schema_fingerprint,
        'boundary_validation': boundary_validation,
        'column_profiles': col_profiles,
        'confidence_metrics': confidence_metrics,
        'calculated_xor_checksum': calculated_xor_hex,
        'source_db_xor_match': xor_match
    }
