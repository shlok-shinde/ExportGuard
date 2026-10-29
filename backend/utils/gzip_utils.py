"""
Low-level GZIP stream inspector and RFC 1952 header/trailer parser.
Handles 4GB ISIZE modulo 2^32 wrap-around conditions.
"""
import struct
import subprocess
from typing import Dict, Any

def inspect_gzip_container(gz_path: str) -> Dict[str, Any]:
    """
    Validates GZIP magic bytes, parses the 8-byte trailer (CRC32, ISIZE),
    runs `gzip -t` in-memory test, and flags 4GB overflow conditions.
    """
    result: Dict[str, Any] = {
        'valid_magic': False,
        'compression_method': None,
        'flags': None,
        'stored_crc32': None,
        'stored_isize': None,
        'isize_wrapped_4gb': False,
        'gzip_t_passed': False,
        'gzip_t_error': None,
        'file_size_bytes': 0,
    }
    
    with open(gz_path, 'rb') as f:
        # Seek end to get file size
        f.seek(0, 2)
        result['file_size_bytes'] = f.tell()
        
        if result['file_size_bytes'] < 18:
            result['gzip_t_error'] = 'File too small to be a valid GZIP container (< 18 bytes)'
            return result
        
        # Read header (first 10 bytes)
        f.seek(0)
        header = f.read(10)
        if header[:2] == b'\x1f\x8b':
            result['valid_magic'] = True
            result['compression_method'] = 'DEFLATE (0x08)' if header[2] == 8 else f'Unknown (0x{header[2]:02x})'
            result['flags'] = header[3]
        
        # Read trailer (last 8 bytes)
        f.seek(-8, 2)
        trailer = f.read(8)
        crc32_val, isize_val = struct.unpack('<II', trailer)
        result['stored_crc32'] = f'0x{crc32_val:08x}'
        result['stored_isize'] = isize_val
        
        # Check 4GB wrap condition:
        # If compressed size is > 500MB and ISIZE is small or 0, it almost certainly wrapped
        if isize_val == 0 and result['file_size_bytes'] > 1024 * 1024:
            result['isize_wrapped_4gb'] = True
        elif result['file_size_bytes'] > isize_val and isize_val > 0:
            # When compressed size exceeds stored ISIZE, modulo 2^32 has wrapped
            result['isize_wrapped_4gb'] = True

    # Run gzip -t
    try:
        proc = subprocess.run(['gzip', '-t', gz_path], capture_output=True, text=True)
        if proc.returncode == 0:
            result['gzip_t_passed'] = True
        else:
            result['gzip_t_passed'] = False
            result['gzip_t_error'] = proc.stderr.strip() or 'GZIP trailer verification failed'
    except Exception as e:
        result['gzip_t_passed'] = False
        result['gzip_t_error'] = str(e)
        
    return result
