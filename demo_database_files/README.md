# 📂 ExportGuard — Judge Demonstration File Suite

This directory contains standalone, production-scale sample database archives and execution logs explicitly engineered to demonstrate ExportGuard's zero-footprint integrity verification engine live to the judges.

---

## ⚡ Quick Demonstration Matrix

| Case | Scenario Name | Upload `.gz` Archive | Upload `.log` File | Expected Verdict | Key Technical Proof for the Judges |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **01** | **The Paradox** (+30% Rows, -20% Size) | `01_case_the_paradox_high_compression.gz` | `01_case_the_paradox_expdp.log` | **INTACT** (Verified) | Shannon entropy drops to **5.21 b/byte**, proving repetitive data triggered maximal LZ77 back-references. Explains management's paradox! |
| **02** | ⭐ **Silent Pipe Truncation** (The Showstopper) | `02_case_pipe_truncated_silent_kill.gz` | `02_case_pipe_aborted_sigkill.log` | **CORRUPTED** (Showstopper) | Standard `gzip -t` returns **0 PASS**! ExportGuard catches missing stream sentinel & detects only 70k of 100k rows. |
| **03** | **Valid Baseline Export** (100k Rows) | `03_case_valid_baseline_100k_rows.gz` | `03_case_valid_expdp.log` | **INTACT** (Certified) | Full 100k row validation, NIST 100% confidence, valid XOR checksum & Merkle tree. |
| **04** | **Raw Truncated Container** (Interrupted Stream) | `04_case_raw_truncated_container.gz` | *(None)* | **CORRUPTED** (Damaged) | Fails Tier 1 in sub-seconds. Container severed midway without RFC 1952 trailer. |
| **05** | **Bit-Rot / CRC Mismatch** (Storage Corruption) | `05_case_bit_rot_crc_corrupted.gz` | *(None)* | **CORRUPTED** (CRC Error) | Detects bit flips in storage media. Decompressed CRC-32 does not match container header. |
| **06** | **Snapshot Too Old** (Oracle ORA-01555) | `06_case_ora1555_snapshot_too_old.gz` | `06_case_ora1555_error.log` | **CORRUPTED** (DB Abort) | Log analyzer flags `ORA-01555: snapshot too old` & `ORA-31693` query failure during extract. |

---

## 🎯 How to Demo to the Judges in the UI

1. Open the Operational Workbench at **`http://127.0.0.1:8080/`**.
2. Scroll to the bottom shelf: **`AUDIT CUSTOM DATABASE DUMP`**.
3. Click **`SELECT .GZ ARCHIVE`** and select any `.gz` file from this folder (`demo_database_files/`).
4. Click **`SELECT LOG FILE`** (optional) and select the corresponding `.log` file.
5. Click **`EXECUTE AUDIT →`**.
6. Watch the three-tier zero-footprint pipeline evaluate the stream in real-time, generate the cryptographic Merkle root, calculate NIST statistical confidence bounds, and stamp the authoritative verdict!
7. Click the top-right **`[ 02 / PULL AUDIT TICKET ]`** button to reveal the perforated tamper-proof restore certificate!

---

## 🔬 Deep Technical Details per Test Case

### Case 1: The Paradox (+30% Rows, -20% Size)
- **Problem Context**: Management observed row count increased from 100,000 to 130,000 (+30%), but compressed archive size shrank from 2.0 MB to ~0.39 MB (-80%). Management suspected data corruption.
- **Forensic Discovery**:
  - The rows consist of automated corporate batch sweep transactions (`ACC-CORP-PRIMARY-001`, `BATCH_AUTOMATED_RECONCILED`).
  - DEFLATE's 32 KiB LZ77 sliding window achieves maximum match lengths (258 bytes per pointer).
  - Shannon entropy drops to **5.21 bits/byte** (vs typical 7.4 b/byte).
  - Stream completion sentinel `__DUMP_COMPLETED_SUCCESSFULLY__` is 100% present and verified.
- **Verdict**: **INTACT** (Verified Repetitive Data Compression).

### Case 2: Silent Pipe Truncation (The Showstopper Failure)
- **Problem Context**: Database export was piped directly into gzip: `expdp ... | gzip > backup.gz`. Midway through (at row 70,000), the database export process was terminated by an OOM/SIGKILL.
- **The Blind Spot**: Gzip received standard EOF from the severed pipe. It flushed its buffers, computed valid CRC-32 and ISIZE for the data received, and exited with **status code 0**.
- **Conventional Failure**: Running `gzip -t backup.gz` returns exit code **0 PASS**! Traditional tools report backup is healthy!
- **ExportGuard Discovery**:
  - Tier 1 checks the uncompressed stream sentinel: **MISSING (TRUNCATED)**!
  - Tier 1 log parser extracts `Killed by signal 9 (SIGKILL)`.
  - Tier 2 streaming row counter identifies 70,000 rows (shortfall of 30,000 rows).
- **Verdict**: **CORRUPTED (SILENT PIPE TRUNCATION DETECTED)**.

### Case 3: Valid Baseline Production Export (100,000 Rows)
- **Context**: Standard nightly production export with diverse financial transactions across multiple currencies and statuses.
- **Metrics**: 100,001 rows (including sentinel), 1.75 MB compressed size, normal entropy (7.39 b/byte), 100% NIST detection confidence.
- **Verdict**: **INTACT (CERTIFIED FOR RESTORE)**.

### Case 4: Raw Truncated Gzip Container
- **Context**: Backup copy was interrupted midway by network timeout or disk full condition.
- **Discovery**: Tier 1 executes sub-second envelope checks. Archive is missing the mandatory 8-byte RFC 1952 trailer (CRC32 and ISIZE).
- **Verdict**: **CORRUPTED (GZIP CONTAINER STRUCTURE DAMAGED)**.

### Case 5: Bit-Rot / Storage Media Corruption
- **Context**: Silent disk bit flips or cosmic ray corruption occurred while the export rested on secondary storage.
- **Discovery**: Gzip container header is intact, but streaming DEFLATE CRC-32 evaluation reveals stored CRC does not match decompressed payload CRC.
- **Verdict**: **CORRUPTED (BIT-ROT / CRC CHECKSUM MISMATCH)**.

### Case 6: Snapshot Too Old (ORA-01555 Rollback Exhaustion)
- **Context**: Long-running export transaction failed read-consistency because UNDO tablespace was overwritten during export.
- **Discovery**: Log parser flags Oracle error codes `ORA-31693` and `ORA-01555`. Sentinel is missing.
- **Verdict**: **CORRUPTED (DATABASE ENGINE QUERY FAILURE)**.
