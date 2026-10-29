#!/usr/bin/env python3
"""
Custom Database Demo Fixture Generator for Judge Demonstrations.
Creates dedicated, clearly-labeled database export archives and log files in
the demo_database_files/ folder for live demonstration to the judges.
"""
import os
import gzip
import csv
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO_DIR = os.path.join(BASE_DIR, 'demo_database_files')

def ensure_demo_dir():
    os.makedirs(DEMO_DIR, exist_ok=True)

def generate_valid_baseline(path: str, rows: int = 100000):
    print(f"[DEMO] Generating Case 3: Valid Baseline ({rows:,} rows) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(rows):
            tx_id = f"TX-{i:08d}-{random.randint(100000, 999999)}"
            acct = f"ACC-{random.randint(10000, 99999)}"
            amt = round(random.uniform(10.0, 5000.0), 2)
            curr = random.choice(['USD', 'EUR', 'GBP', 'JPY', 'CAD'])
            status = random.choice(['SETTLED', 'PENDING', 'FLAGGED_REVIEW'])
            note = f"Retail terminal POS payment at gateway node {random.randint(1, 20)}"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        writer.writerow(['__DUMP_COMPLETED_SUCCESSFULLY__', 'SENTINEL', '0.00', 'SYS', 'COMPLETED', 'Job completed cleanly'])

def generate_the_paradox(path: str, rows: int = 130000):
    print(f"[DEMO] Generating Case 1: The Paradox ({rows:,} rows, low entropy) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(rows):
            tx_id = f"TX-{i:08d}"
            acct = "ACC-CORP-PRIMARY-001"
            amt = 100.00
            curr = "USD"
            status = "BATCH_AUTOMATED_RECONCILED"
            note = "Standard batch sweep routine for corporate liquidity account pool - automated reconciliation rule 4B"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        writer.writerow(['__DUMP_COMPLETED_SUCCESSFULLY__', 'SENTINEL', '0.00', 'SYS', 'COMPLETED', 'Job completed cleanly'])

def generate_pipe_truncated(path: str, cut_at_row: int = 70000):
    print(f"[DEMO] Generating Case 2: Silent Pipe Truncation ({cut_at_row:,} rows, NO SENTINEL) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(cut_at_row):
            tx_id = f"TX-{i:08d}-{random.randint(100000, 999999)}"
            acct = f"ACC-{random.randint(10000, 99999)}"
            amt = round(random.uniform(10.0, 5000.0), 2)
            curr = random.choice(['USD', 'EUR', 'GBP'])
            status = random.choice(['SETTLED', 'PENDING'])
            note = f"Automated payment batch processing at terminal {random.randint(1, 10)}"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        # Crucial: NO sentinel is written. Stream ends abruptly, but gzip closes cleanly!

def generate_raw_truncated(valid_path: str, target_path: str):
    print(f"[DEMO] Generating Case 4: Raw Truncated Gzip Container -> {os.path.basename(target_path)}...")
    with open(valid_path, 'rb') as f:
        data = f.read()
    # Keep 70% of compressed bytes (severs RFC 1952 8-byte trailer)
    cut = int(len(data) * 0.7)
    with open(target_path, 'wb') as f:
        f.write(data[:cut])

def generate_bit_rot(valid_path: str, target_path: str):
    print(f"[DEMO] Generating Case 5: Bit-Rot Corrupted Archive -> {os.path.basename(target_path)}...")
    with open(valid_path, 'rb') as f:
        data = bytearray(f.read())
    # Flip bits across 32 bytes in the center
    mid = len(data) // 2
    for offset in range(mid, mid + 32):
        data[offset] ^= 0xFF
    with open(target_path, 'wb') as f:
        f.write(data)

def generate_ora1555_export(path: str, cut_at_row: int = 42000):
    print(f"[DEMO] Generating Case 6: Snapshot Too Old Export ({cut_at_row:,} rows) -> {os.path.basename(path)}...")
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['transaction_id', 'account_id', 'amount', 'currency', 'status', 'payload_note'])
        for i in range(cut_at_row):
            tx_id = f"TX-ORA-{i:08d}"
            acct = f"ACC-CORP-{random.randint(100, 999)}"
            amt = round(random.uniform(50.0, 2500.0), 2)
            curr = "USD"
            status = "PENDING_SNAPSHOT"
            note = "Long running analytical extract transaction ledger record"
            writer.writerow([tx_id, acct, amt, curr, status, note])
        # No sentinel because DB query aborted with ORA-01555

def generate_demo_logs():
    print("[DEMO] Generating demo database logs...")
    
    # 1. Paradox log
    with open(os.path.join(DEMO_DIR, '01_case_the_paradox_expdp.log'), 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Thu Oct 29 18:30:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_REPETITIVE_01": schemas=TREASURY
. . exported "TREASURY"."LIQUIDITY_SWEEP_TX"           12.4 MB  130000 rows in 2 seconds
Master table "SYSTEM"."SYS_EXPORT_REPETITIVE_01" successfully loaded/unloaded
Dump file set for SYSTEM.SYS_EXPORT_REPETITIVE_01 is:
  /u01/app/oracle/dpdump/export_liquidity.dmp
Job "SYSTEM"."SYS_EXPORT_REPETITIVE_01" successfully completed at Thu Oct 29 18:30:04 2026
""")

    # 2. Pipe aborted log
    with open(os.path.join(DEMO_DIR, '02_case_pipe_aborted_sigkill.log'), 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Thu Oct 29 18:45:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_FINANCE": schemas=FINANCE
Processing object type SCHEMA_EXPORT/TABLE/TABLE
. . exported "FINANCE"."TRANSACTIONS"                    29.1 MB   70000 rows
Killed by signal 9 (SIGKILL)
""")

    # 3. Valid Baseline log
    with open(os.path.join(DEMO_DIR, '03_case_valid_expdp.log'), 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Thu Oct 29 18:00:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_BASELINE": schemas=FINANCE
. . exported "FINANCE"."TRANSACTIONS"                    42.5 MB  100000 rows in 4 seconds
Master table "SYSTEM"."SYS_EXPORT_BASELINE" successfully loaded/unloaded
Dump file set for SYSTEM.SYS_EXPORT_BASELINE is:
  /u01/app/oracle/dpdump/export_baseline.dmp
Job "SYSTEM"."SYS_EXPORT_BASELINE" successfully completed at Thu Oct 29 18:00:06 2026
""")

    # 6. ORA-1555 log
    with open(os.path.join(DEMO_DIR, '06_case_ora1555_error.log'), 'w') as f:
        f.write("""Export: Release 19.0.0.0.0 - Production on Thu Oct 29 19:15:00 2026
Connected to: Oracle Database 19c Enterprise Edition Release 19.3.0.0.0
Starting "SYSTEM"."SYS_EXPORT_LEDGER": schemas=FINANCE
Processing object type SCHEMA_EXPORT/TABLE/TABLE
. . exporting table "FINANCE"."GENERAL_LEDGER"
ORA-31693: Table data object "FINANCE"."GENERAL_LEDGER" failed to load/unload
ORA-01555: snapshot too old: rollback segment number 14 with name "_SYSSMU14$" too small
Job "SYSTEM"."SYS_EXPORT_LEDGER" completed with 2 error(s) at Thu Oct 29 19:15:42 2026
""")

def main():
    ensure_demo_dir()
    
    p1 = os.path.join(DEMO_DIR, '01_case_the_paradox_high_compression.gz')
    p2 = os.path.join(DEMO_DIR, '02_case_pipe_truncated_silent_kill.gz')
    p3 = os.path.join(DEMO_DIR, '03_case_valid_baseline_100k_rows.gz')
    p4 = os.path.join(DEMO_DIR, '04_case_raw_truncated_container.gz')
    p5 = os.path.join(DEMO_DIR, '05_case_bit_rot_crc_corrupted.gz')
    p6 = os.path.join(DEMO_DIR, '06_case_ora1555_snapshot_too_old.gz')
    
    generate_the_paradox(p1, rows=130000)
    generate_pipe_truncated(p2, cut_at_row=70000)
    generate_valid_baseline(p3, rows=100000)
    generate_raw_truncated(p3, p4)
    generate_bit_rot(p3, p5)
    generate_ora1555_export(p6, cut_at_row=42000)
    generate_demo_logs()
    
    print("\n=======================================================")
    print("✅ Judge Demo Database Files Successfully Generated in:")
    print(f"   {DEMO_DIR}")
    print("=======================================================")
    for fn in sorted(os.listdir(DEMO_DIR)):
        fp = os.path.join(DEMO_DIR, fn)
        if os.path.isfile(fp):
            sz = os.path.getsize(fp)
            print(f"  - {fn:45s} ({sz:8,d} bytes)")

if __name__ == '__main__':
    main()
