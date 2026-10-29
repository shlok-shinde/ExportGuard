"""
Shannon Entropy Analysis Module.
Computes byte-level entropy and sliding-window profiles to detect
zeroed blocks (bit rot), repeated blocks (DMA stutter), and foreign noise injection.
"""
import math
import gzip
from collections import Counter
from typing import Dict, Any, List

def compute_shannon_entropy(data: bytes) -> float:
    """Calculates byte-level Shannon entropy in bits per byte [0.0 - 8.0]."""
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 4)

def sliding_window_entropy_analysis(
    gz_path: str,
    window_size: int = 4096,
    step_size: int = 1024,
    max_windows: int = 1000
) -> Dict[str, Any]:
    """
    Computes sliding-window entropy across uncompressed stream.
    Identifies localized corruption anomalies:
    - ZEROED_BLOCK: H drops near 0.0 (bit rot, sparse extent allocation error)
    - REPEATED_BLOCK: H drops <= 2.0 (repeating patterns)
    - NOISE_INJECTION: H spikes to > 7.95 in expected structured text (4.0 - 5.5)
    """
    profile: List[Dict[str, Any]] = []
    anomalies: List[Dict[str, Any]] = []
    
    with gzip.open(gz_path, 'rb') as f:
        buffer = bytearray()
        offset = 0
        window_idx = 0
        
        while window_idx < max_windows:
            needed = window_size - len(buffer)
            if needed > 0:
                chunk = f.read(max(needed, 65536))
                if not chunk:
                    break
                buffer.extend(chunk)
                
            if len(buffer) < window_size:
                # Remaining tail is smaller than window
                if len(buffer) > 256:
                    h = compute_shannon_entropy(bytes(buffer))
                    profile.append({'offset': offset, 'entropy': h})
                break
                
            window = bytes(buffer[:window_size])
            h = compute_shannon_entropy(window)
            profile.append({'offset': offset, 'entropy': h})
            
            # Anomaly Classification
            if h <= 0.2:
                anomalies.append({
                    'offset': offset,
                    'entropy': h,
                    'type': 'ZEROED_BLOCK',
                    'severity': 'CRITICAL',
                    'detail': 'Zeroed or flat uniform block detected (potential bit rot or lost extent).'
                })
            elif h <= 1.8:
                anomalies.append({
                    'offset': offset,
                    'entropy': h,
                    'type': 'REPEATED_BLOCK',
                    'severity': 'WARNING',
                    'detail': 'Severely repetitive byte sequence or firmware ring-buffer stutter.'
                })
            elif h >= 7.95:
                anomalies.append({
                    'offset': offset,
                    'entropy': h,
                    'type': 'NOISE_INJECTION',
                    'severity': 'WARNING',
                    'detail': 'Extremely high entropy segment resembling random/encrypted payload in structured dump.'
                })
                
            buffer = buffer[step_size:]
            offset += step_size
            window_idx += 1

    entropies = [p['entropy'] for p in profile]
    avg_entropy = round(sum(entropies) / len(entropies), 4) if entropies else 0.0
    
    return {
        'total_windows_evaluated': len(profile),
        'window_size_bytes': window_size,
        'step_size_bytes': step_size,
        'average_entropy': avg_entropy,
        'min_entropy': min(entropies) if entropies else 0.0,
        'max_entropy': max(entropies) if entropies else 0.0,
        'anomalies_detected': len(anomalies),
        'anomalies': anomalies[:25],  # Cap response payload
        'profile_sample': profile[::max(1, len(profile) // 60)], # 60 points for charting
    }
