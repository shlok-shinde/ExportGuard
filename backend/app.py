"""
ExportGuard FastAPI Backend Server.
Provides API endpoints for database export integrity analysis and demo simulation.
"""
import os
import shutil
import tempfile
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from backend.analyzers.tier1_envelope import run_tier1
from backend.analyzers.tier2_sampling import run_tier2
from backend.analyzers.tier3_forensic import run_tier3
from backend.analyzers.report_generator import generate_full_report

app = FastAPI(
    title="ExportGuard API",
    description="Zero-Footprint Compressed Database Export Integrity Verification Engine",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
FIXTURES_DIR = os.path.join(BASE_DIR, 'tests', 'fixtures')

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "ExportGuard Engine", "version": "2.0.0"}

@app.get("/api/demo/{scenario}")
def run_demo_scenario(scenario: str):
    """
    Runs one of the 5 pre-packaged realistic scenarios:
    - 'valid': Standard export, fully intact
    - 'pipe_truncated': SHOWSTOPPER (gzip -t passes, sentinel fails)
    - 'high_compression': Problem statement (+30% rows, -20% size innocent case)
    - 'raw_truncated': Cut byte stream (gzip -t fails)
    - 'corrupted': Bit-flipped bytes (CRC fails)
    """
    scenario_files = {
        'valid': ('valid_export.gz', 'valid_expdp.log', 100000, 100000, 2004185),
        'pipe_truncated': ('pipe_truncated_export.gz', 'pipe_aborted.log', 100000, 100000, 2004185),
        'high_compression': ('high_compression_export.gz', 'valid_expdp.log', 130000, 100000, 2004185),
        'raw_truncated': ('truncated_export.gz', None, 100000, 100000, 2004185),
        'corrupted': ('corrupted_export.gz', None, 100000, 100000, 2004185),
    }
    
    if scenario not in scenario_files:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario}' not found. Choose from {list(scenario_files.keys())}")
        
    gz_name, log_name, curr_rows, prev_rows, prev_size = scenario_files[scenario]
    gz_path = os.path.join(FIXTURES_DIR, gz_name)
    log_path = os.path.join(FIXTURES_DIR, log_name) if log_name else None
    
    if not os.path.exists(gz_path):
        raise HTTPException(status_code=500, detail="Test fixture not generated. Run scripts/generate_test_data.py first.")
        
    # Execute 3 Tiers
    t1 = run_tier1(
        gz_path=gz_path,
        log_path=log_path,
        prev_size_bytes=prev_size,
        curr_rows=curr_rows,
        prev_rows=prev_rows
    )
    
    t2 = None
    t3 = None
    
    # If container is readable, run Tier 2 & Tier 3
    if t1['gzip_container']['gzip_t_passed']:
        t2 = run_tier2(gz_path)
        t3 = run_tier3(gz_path)
        
    report = generate_full_report(
        filename=gz_name,
        tier1=t1,
        tier2=t2,
        tier3=t3
    )
    return report

@app.post("/api/analyze")
async def analyze_upload(
    export_file: UploadFile = File(...),
    log_file: Optional[UploadFile] = File(None),
    curr_rows: Optional[int] = Form(130000),
    prev_rows: Optional[int] = Form(100000),
    prev_size_bytes: Optional[int] = Form(2000000)
):
    """Analyzes an uploaded .gz export and optional log file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gz_path = os.path.join(tmp_dir, export_file.filename)
        with open(gz_path, "wb") as buffer:
            shutil.copyfileobj(export_file.file, buffer)
            
        log_path = None
        if log_file and log_file.filename:
            log_path = os.path.join(tmp_dir, log_file.filename)
            with open(log_path, "wb") as buffer:
                shutil.copyfileobj(log_file.file, buffer)
                
        t1 = run_tier1(
            gz_path=gz_path,
            log_path=log_path,
            prev_size_bytes=prev_size_bytes,
            curr_rows=curr_rows,
            prev_rows=prev_rows
        )
        
        t2 = None
        t3 = None
        if t1['gzip_container']['gzip_t_passed']:
            t2 = run_tier2(gz_path)
            t3 = run_tier3(gz_path)
            
        report = generate_full_report(
            filename=export_file.filename,
            tier1=t1,
            tier2=t2,
            tier3=t3
        )
        return report

# Serve frontend static assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "ExportGuard API operational. Frontend under construction."}

@app.get("/landing")
def serve_landing():
    landing_file = os.path.join(FRONTEND_DIR, 'landing.html')
    if os.path.exists(landing_file):
        return FileResponse(landing_file)
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))

@app.get("/receipt")
def serve_receipt():
    receipt_file = os.path.join(FRONTEND_DIR, 'receipt.html')
    if os.path.exists(receipt_file):
        return FileResponse(receipt_file)
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))

