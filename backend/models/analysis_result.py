"""
Pydantic data models for ExportGuard analysis requests and reports.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Tier1Report(BaseModel):
    passed: bool
    sentinel_check: Dict[str, Any]
    gzip_container: Dict[str, Any]
    log_parser: Optional[Dict[str, Any]] = None
    anomaly_scorer: Dict[str, Any]

class Tier2Report(BaseModel):
    passed: bool
    streaming_row_count: int
    header_fingerprint: str
    boundary_validation: Dict[str, Any]
    column_profiles: List[Dict[str, Any]]
    confidence_metrics: Dict[str, Any]
    source_db_xor_match: Optional[bool] = None

class Tier3Report(BaseModel):
    passed: bool
    entropy_analysis: Dict[str, Any]
    block_merkle_verification: Dict[str, Any]

class FullAnalysisReport(BaseModel):
    job_id: str
    export_filename: str
    timestamp: str
    verdict: str = Field(description="INTACT, SUSPICIOUS, or CORRUPTED")
    verdict_severity: str = Field(description="SUCCESS, WARNING, or CRITICAL")
    verdict_summary: str
    root_cause_explanation: str
    tier1: Tier1Report
    tier2: Optional[Tier2Report] = None
    tier3: Optional[Tier3Report] = None
