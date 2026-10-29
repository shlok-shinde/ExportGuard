"""
Sentinel detection utilities for export stream completion.
Addresses the #1 failure mode identified in research:
When an export process is killed mid-pipe (SIGTERM/SIGKILL/OOM), gzip receives
a normal EOF, cleanly writes an RFC 1952 trailer (CRC-32 + ISIZE), and exits 0.
gzip -t passes completely, but the dataset is truncated!
"""
import gzip
from collections import deque
from typing import Dict, Any, List

KNOWN_SENTINELS = [
    # Custom backup scripts hardened sentinel
    '__DUMP_COMPLETED_SUCCESSFULLY__',
    # Oracle expdp / Data Pump completion indicators
    'Job "SYSTEM"."SYS_EXPORT',
    'successfully completed',
    'Master table',
    # PostgreSQL pg_dump indicators
    'PostgreSQL database dump complete',
    '\\.',  # Standard PostgreSQL COPY EOF marker
    # MySQL mysqldump
    'Dump completed on',
]

def check_sentinel(gz_path: str, tail_lines_to_check: int = 30) -> Dict[str, Any]:
    """
    Checks the last N lines of the uncompressed stream for completion markers.
    Streams through without loading the full file into memory.
    """
    try:
        with gzip.open(gz_path, 'rt', errors='replace') as f:
            tail = deque(f, maxlen=tail_lines_to_check)
            
        tail_list = [line.strip() for line in tail]
        tail_text = '\n'.join(tail_list)
        
        found_sentinels = [s for s in KNOWN_SENTINELS if s in tail_text]
        
        # Check for crash or termination signatures in tail
        aborted_markers = ['ORA-', 'FATAL:', 'Traceback', 'core dumped', 'Killed', 'Terminated', 'PGRES_FATAL_ERROR']
        found_aborts = [m for m in aborted_markers if m in tail_text]
        
        if found_aborts:
            return {
                'status': 'FAIL',
                'severity': 'CRITICAL',
                'passed': False,
                'found_sentinel': None,
                'found_aborts': found_aborts,
                'message': f'Export data stream contains fatal crash markers: {", ".join(found_aborts)}',
                'tail_lines': tail_list[-5:]
            }

        if not found_sentinels:
            return {
                'status': 'FAIL',
                'severity': 'CRITICAL',
                'passed': False,
                'found_sentinel': None,
                'found_aborts': [],
                'message': (
                    'No completion sentinel found in stream footer. '
                    'The export process was likely killed mid-pipe while gzip was running. '
                    'gzip -t cannot catch this because gzip received EOF and wrote a valid trailer.'
                ),
                'tail_lines': tail_list[-5:]
            }
            
        return {
            'status': 'PASS',
            'severity': 'INFO',
            'passed': True,
            'found_sentinel': found_sentinels[0],
            'found_aborts': [],
            'message': f'Valid completion sentinel verified: "{found_sentinels[0]}"',
            'tail_lines': tail_list[-3:]
        }
    except Exception as e:
        return {
            'status': 'FAIL',
            'severity': 'CRITICAL',
            'passed': False,
            'found_sentinel': None,
            'found_aborts': [],
            'message': f'Failed to inspect footer stream: {str(e)}',
            'tail_lines': []
        }
