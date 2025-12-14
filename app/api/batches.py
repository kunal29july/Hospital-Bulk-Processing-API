# ============================================================================
# BATCHES ROUTER - Batch Query Endpoints
# ============================================================================
# This router handles batch listing and detail retrieval operations
# 
# ENDPOINTS:
# - GET /batches → list_batches()
# - GET /batches/{batch_id} → get_batch_details()
# 
# FLOW: Called from app/main.py → Queries database → Returns batch info
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import BatchUpload, HospitalProcessingResult
from app.schemas import BulkUploadResponse, HospitalProcessingDetail, BatchSummary

router = APIRouter()


@router.get("/batches", response_model=List[BatchSummary])
async def list_batches(db: Session = Depends(get_db)):
    """
    List all batch uploads with summary information
    
    FLOW:
    1. Query database for all BatchUpload records
    2. Return list ordered by creation date (newest first)
    
    GOES TO:
    - app/database.py → Database query via get_db()
    - app/models.py::BatchUpload → Database model
    """
    # FLOW → app/models.py::BatchUpload query → Database
    batches = db.query(BatchUpload).order_by(BatchUpload.created_at.desc()).all()
    return batches


@router.get("/batches/{batch_id}", response_model=BulkUploadResponse)
async def get_batch_details(batch_id: str, db: Session = Depends(get_db)):
    """
    Get detailed results for a specific batch including all hospital records
    
    FLOW:
    1. Query BatchUpload by batch_id
    2. Query all HospitalProcessingResult records for this batch
    3. Return detailed response with all hospital processing details
    
    GOES TO:
    - app/database.py → Database queries via get_db()
    - app/models.py::BatchUpload, HospitalProcessingResult → Database models
    """
    # FLOW → app/models.py::BatchUpload query → Database
    batch = db.query(BatchUpload).filter(BatchUpload.batch_id == batch_id).first()
    
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get all hospital results for this batch
    # FLOW → app/models.py::HospitalProcessingResult query → Database
    results = db.query(HospitalProcessingResult).filter(
        HospitalProcessingResult.batch_upload_id == batch.id
    ).order_by(HospitalProcessingResult.row_number).all()
    
    processing_details = [
        HospitalProcessingDetail(
            row=result.row_number,
            hospital_id=result.hospital_id,
            name=result.name,
            status=result.status.value,
            error_message=result.error_message
        )
        for result in results
    ]
    
    return BulkUploadResponse(
        batch_id=batch.batch_id,
        total_hospitals=batch.total_hospitals,
        processed_hospitals=batch.processed_hospitals,
        failed_hospitals=batch.failed_hospitals,
        processing_time_seconds=batch.processing_time_seconds or 0.0,
        batch_activated=batch.batch_activated,
        hospitals=processing_details
    )
