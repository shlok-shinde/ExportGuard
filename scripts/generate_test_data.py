#!/usr/bin/env python3
"""
Test Fixture Generator for ExportGuard.
Generates realistic compressed database exports representing:
1. valid_export.gz (baseline 100k rows, normal entropy, with sentinel)
2. pipe_truncated_export.gz (THE SHOWSTOPPER: 70k rows, gzip -t PASSES, but sentinel MISSING)
3. high_compression_export.gz (+30% rows, repetitive low-entropy, 20% smaller, with sentinel)
4. truncated_export.gz (severed byte stream, gzip -t FAILS)
5. corrupted_export.gz (bit-flipped block, CRC FAILS)
And accompanying Oracle Data Pump / Postgres log files.
"""
import os
import gzip
import csv
import random

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', 'fixtures')

def ensure_dir():
    os.makedirs(FIXTURES_DIR, exist_ok=True)

def generate_valid_export(path: str, rows: int = 100000):
    """Generates baseline export with diverse (high entropy) data."""
    print(f"Generating valid export ({rows:,} rows) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(rows):
            # High variance
            tx_id = f"TX-{i:08d}-{random.randint(100000, 999999)}"
            acct = f"ACC-{random.randint(10000, 99999)}"
            amt = round(random.uniform(5.0, 9500.0), 2)
            curr = random.choice(['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CHF', 'AUD'])
            status = random.choice(['SETTLED', 'PENDING', 'FLAGGED_REVIEW', 'REFUNDED', 'CHARGED_BACK'])
            note = f"Standard user clearing via terminal #{random.randint(10, 99)} at auth zone {random.randint(1, 15)}"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        # Append valid sentinel
        writer.writerow(['__DUMP_COMPLETED_SUCCESSFULLY__', 'SENTINEL', '0.00', 'SYS', 'COMPLETED', 'Job completed cleanly'])

def generate_pipe_truncated_export(path: str, target_rows: int = 100000, cut_at_row: int = 70000):
    """
    ⭐ THE SHOWSTOPPER TEST FIXTURE:
    Simulates pipe termination: export process crashed after 70,000 rows.
    gzip cleanly received EOF, flushed buffer, computed CRC & ISIZE, and appended trailer.
    gzip -t PASSES 100% with exit code 0! But sentinel is absent and 30,000 rows are missing!
    """
    print(f"Generating pipe-truncated export (cut at {cut_at_row:,} rows) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(cut_at_row):
            tx_id = f"TX-{i:08d}-{random.randint(100000, 999999)}"
            acct = f"ACC-{random.randint(10000, 99999)}"
            amt = round(random.uniform(5.0, 9500.0), 2)
            curr = random.choice(['USD', 'EUR', 'GBP', 'JPY', 'CAD'])
            status = random.choice(['SETTLED', 'PENDING', 'FLAGGED_REVIEW'])
            note = f"Standard user clearing via terminal #{random.randint(10, 99)}"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        # NO SENTINEL APPENDED! Stream abruptly ends.

def generate_high_compression_export(path: str, rows: int = 130000):
    """
    Innocent scenario: 30% more rows (130,000 vs 100,000), but highly repetitive templated data.
    Shannon entropy drops significantly -> gzip LZ77 achieves huge back-references -> file size shrinks 20-30%!
    """
    print(f"Generating high-compression export ({rows:,} rows, repetitive data) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(rows):
            # Extremely repetitive data
            tx_id = f"TX-{i:08d}"
            acct = "ACC-CORP-PRIMARY-001"
            amt = 100.00
            curr = "USD"
            status = "BATCH_AUTOMATED_RECONCILED"
            note = "Standard batch sweep routine for corporate liquidity account pool - automated reconciliation rule 4B"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        writer.writerow(['__DUMP_COMPLETED_SUCCESSFULLY__', 'SENTINEL', '0.00', 'SYS', 'COMPLETED', 'Job completed cleanly'])

def generate_truncated_export(valid_path: str, target_path: str):
    """Raw truncated container: truncates byte file midway so gzip -t FAILS."""
    print(f"Generating raw truncated export -> {os.path.basename(target_path)}...")
    with open(valid_path, 'rb') as f:
        data = f.read()
    # Keep 70% of raw bytes, dropping trailer
    cut = int(len(data) * 0.7)
    with open(target_path, 'wb') as f:
        f.write(data[:cut])

def generate_corrupted_export(valid_path: str, target_path: str):
    """Bit-flipped container: flips bytes in compressed stream so CRC check FAILS."""
    print(f"Generating bit-flipped corrupted export -> {os.path.basename(target_path)}...")
    with open(valid_path, 'rb') as f:
        data = bytearray(f.read())
    # Flip bytes in middle
    mid = len(data) // 2
    for offset in range(mid, mid + 20):
        data[offset] ^= 0xFF
    with open(target_path, 'wb') as f:
        f.write(data)

def generate_log_files():
    valid_log = os.path.join(FIXTURES_DIR, 'valid_expdp.log')
    corrupt_log = os.path.join(FIXTURES_DIR, 'corrupt_ora1555.log')
    aborted_log = os.path.join(FIXTURES_DIR, 'pipe_aborted.log')
    
    with open(valid_log, 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Wed Oct 29 14:10:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_SCHEMA_01": schemas=FINANCE
. . exported "FINANCE"."TRANSACTIONS"                    42.5 MB  100000 rows in 3 seconds
Master table "SYSTEM"."SYS_EXPORT_SCHEMA_01" successfully loaded/unloaded
Dump file set for SYSTEM.SYS_EXPORT_SCHEMA_01 is:
  /u01/app/oracle/dpdump/export.dmp
Job "SYSTEM"."SYS_EXPORT_SCHEMA_01" successfully completed at Wed Oct 29 14:10:05 2026
""")

    with open(corrupt_log, 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Wed Oct 29 14:10:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_SCHEMA_01": schemas=FINANCE
ORA-31693: Table data object "FINANCE"."TRANSACTIONS" failed to load/unload
ORA-01555: snapshot too old: rollback segment number 14 with name "_SYSSMU14$" too small
Job "SYSTEM"."SYS_EXPORT_SCHEMA_01" completed with 2 error(s) at Wed Oct 29 14:11:00 2026
""")

    with open(aborted_log, 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Wed Oct 29 14:10:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_SCHEMA_01": schemas=FINANCE
Processing object type SCHEMA_EXPORT/TABLE/TABLE
. . exported "FINANCE"."TRANSACTIONS"                    29.1 MB   70000 rows
Killed by signal 9 (SIGKILL)
""")

def main():
    ensure_dir()
    valid_gz = os.path.join(FIXTURES_DIR, 'valid_export.gz')
    pipe_trunc_gz = os.path.join(FIXTURES_DIR, 'pipe_truncated_export.gz')
    high_comp_gz = os.path.join(FIXTURES_DIR, 'high_compression_export.gz')
    trunc_gz = os.path.join(FIXTURES_DIR, 'truncated_export.gz')
    corrupt_gz = os.path.join(FIXTURES_DIR, 'corrupted_export.gz')
    
    generate_valid_export(valid_gz, rows=100000)
    generate_pipe_truncated_export(pipe_trunc_gz, target_rows=100000, cut_at_row=70000)
    generate_high_compression_export(high_comp_gz, rows=130000)
    generate_truncated_export(valid_gz, trunc_gz)
    generate_corrupted_export(valid_gz, corrupt_gz)
    generate_log_files()
    
    print("\nFixture Summary:")
    for fn in os.listdir(FIXTURES_DIR):
        p = os.path.join(FIXTURES_DIR, fn)
        sz = os.path.getsize(p)
        print(f"  {fn:30s} : {sz:8,d} bytes")
    print("Done!")

if __name__ == '__main__':
    main()
