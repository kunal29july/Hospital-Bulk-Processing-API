# ============================================================================
# API ENDPOINTS - FLOW CONTINUES FROM app/main.py
# ============================================================================
# This file contains all API endpoint handlers for hospital bulk processing
# 
# FLOW FROM main.py:
# Request → CORS Middleware → router (this file) → Endpoint handler
# 
# ENDPOINTS DEFINED HERE:
# 1. POST /hospitals/bulk → bulk_create_hospitals() 
# 2. GET /batches → list_batches()
# 3. GET /batches/{batch_id} → get_batch_details()
# 
# DEPENDENCIES USED:
# - app.database.get_db → Database session management
# - app.services.csv_processor.CSVProcessor → CSV validation & parsing
# - app.services.hospital_client.HospitalAPIClient → External API calls
# - app.models → Database models (BatchUpload, HospitalProcessingResult)
# - app.schemas → Request/Response schemas (Pydantic models)
# ============================================================================

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import time
from datetime import datetime

from app.database import get_db
from app.models import BatchUpload, HospitalProcessingResult, BatchStatus, HospitalStatus
from app.schemas import (
    BulkUploadResponse, 
    HospitalProcessingDetail, 
    BatchSummary,
    HospitalCreate
)
from app.services.csv_processor import CSVProcessor
from app.services.hospital_client import HospitalAPIClient

router = APIRouter()


# ============================================================================
# ENDPOINT 1: POST /hospitals/bulk
# ============================================================================
# Main bulk upload endpoint - handles CSV upload and hospital creation
# 
# FLOW:
# 1. Receive CSV file → CSVProcessor.validate_and_parse_csv()
# 2. Create BatchUpload record in database
# 3. For each row → CSVProcessor.validate_hospital_data()
# 4. For valid rows → HospitalAPIClient.create_hospital() (external API)
# 5. If all succeed → HospitalAPIClient.activate_batch() (external API)
# 6. Update BatchUpload with results
# 7. Return BulkUploadResponse
# 
# GOES TO:
# - app/services/csv_processor.py → CSV validation & parsing
# - app/services/hospital_client.py → External API calls
# - app/database.py → Database operations via get_db()
# ============================================================================
@router.post("/hospitals/bulk", response_model=BulkUploadResponse)
async def bulk_create_hospitals(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Bulk create hospitals from CSV file
    
    CSV Format: name,address,phone (phone is optional)
    Maximum 20 hospitals per upload
    """
    start_time = time.time()
    
    # Step 1: Validate and parse CSV
    # FLOW → app/services/csv_processor.py::validate_and_parse_csv()
    csv_processor = CSVProcessor()
    rows, filename = await csv_processor.validate_and_parse_csv(file)
    
    # Step 2: Generate unique batch ID
    batch_id = str(uuid.uuid4())
    
    # Step 3: Create batch upload record
    # FLOW → app/models.py::BatchUpload model → Database
    batch_upload = BatchUpload(
        batch_id=batch_id,
        filename=filename,
        total_hospitals=len(rows),
        status=BatchStatus.PROCESSING
    )
    db.add(batch_upload)
    db.commit()
    db.refresh(batch_upload)
    
    # Step 4: Process each hospital
    # FLOW → app/services/hospital_client.py for API calls
    hospital_client = HospitalAPIClient()
    processing_results = []
    processed_count = 0
    failed_count = 0
    
    for idx, row in enumerate(rows, start=1):
        # Validate hospital data
        # FLOW → app/services/csv_processor.py::validate_hospital_data()
        is_valid, error_msg = csv_processor.validate_hospital_data(row)
        
        if not is_valid:
            # Record validation failure
            # FLOW → app/models.py::HospitalProcessingResult model → Database
            result = HospitalProcessingResult(
                batch_upload_id=batch_upload.id,
                row_number=idx,
                name=row.get('name', 'Unknown'),
                address=row.get('address', 'Unknown'),
                phone=row.get('phone'),
                status=HospitalStatus.FAILED,
                error_message=error_msg
            )
            db.add(result)
            failed_count += 1
            
            processing_results.append(HospitalProcessingDetail(
                row=idx,
                hospital_id=None,
                name=row.get('name', 'Unknown'),
                status="failed",
                error_message=error_msg
            ))
            continue
        
        # Create hospital via API
        # FLOW → app/schemas.py::HospitalCreate (Pydantic validation)
        hospital_data = HospitalCreate(
            name=row['name'],
            address=row['address'],
            phone=row.get('phone'),
            creation_batch_id=batch_id
        )
        
        # FLOW → app/services/hospital_client.py::create_hospital() → External API
        success, hospital_response, error_message = await hospital_client.create_hospital(hospital_data)
        
        if success:
            # Record success
            result = HospitalProcessingResult(
                batch_upload_id=batch_upload.id,
                row_number=idx,
                hospital_id=hospital_response.id,
                name=hospital_response.name,
                address=hospital_response.address,
                phone=hospital_response.phone,
                status=HospitalStatus.CREATED_AND_ACTIVATED,  # Will be updated after activation
                error_message=None
            )
            db.add(result)
            processed_count += 1
            
            processing_results.append(HospitalProcessingDetail(
                row=idx,
                hospital_id=hospital_response.id,
                name=hospital_response.name,
                status="created_and_activated",
                error_message=None
            ))
        else:
            # Record failure
            result = HospitalProcessingResult(
                batch_upload_id=batch_upload.id,
                row_number=idx,
                hospital_id=None,
                name=row['name'],
                address=row['address'],
                phone=row.get('phone'),
                status=HospitalStatus.FAILED,
                error_message=error_message
            )
            db.add(result)
            failed_count += 1
            
            processing_results.append(HospitalProcessingDetail(
                row=idx,
                hospital_id=None,
                name=row['name'],
                status="failed",
                error_message=error_message
            ))
    
    # Step 5: Activate batch if all succeeded
    batch_activated = False
    
    if failed_count == 0:
        # All hospitals created successfully, activate the batch
        # FLOW → app/services/hospital_client.py::activate_batch() → External API
        activation_success, activation_error = await hospital_client.activate_batch(batch_id)
        
        if activation_success:
            batch_activated = True
            batch_upload.status = BatchStatus.COMPLETED
        else:
            # Activation failed, mark batch as failed
            batch_upload.status = BatchStatus.FAILED
            # Note: Hospitals are already created but not activated
    else:
        # Some hospitals failed, don't activate
        batch_upload.status = BatchStatus.FAILED
    
    # Step 6: Update batch upload record
    batch_upload.processed_hospitals = processed_count
    batch_upload.failed_hospitals = failed_count
    batch_upload.batch_activated = batch_activated
    batch_upload.processing_time_seconds = time.time() - start_time
    batch_upload.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Step 7: Return response
    return BulkUploadResponse(
        batch_id=batch_id,
        total_hospitals=len(rows),
        processed_hospitals=processed_count,
        failed_hospitals=failed_count,
        processing_time_seconds=round(time.time() - start_time, 2),
        batch_activated=batch_activated,
        hospitals=processing_results
    )


# ============================================================================
# ENDPOINT 2: GET /batches
# ============================================================================
# List all batch uploads with summary information
# 
# FLOW:
# 1. Query database for all BatchUpload records
# 2. Return list ordered by creation date (newest first)
# 
# GOES TO:
# - app/database.py → Database query via get_db()
# - app/models.py::BatchUpload → Database model
# ============================================================================
@router.get("/batches", response_model=List[BatchSummary])
async def list_batches(db: Session = Depends(get_db)):
    """
    List all batch uploads
    """
    # FLOW → app/models.py::BatchUpload query → Database
    batches = db.query(BatchUpload).order_by(BatchUpload.created_at.desc()).all()
    return batches


# ============================================================================
# ENDPOINT 3: GET /batches/{batch_id}
# ============================================================================
# Get detailed results for a specific batch including all hospital records
# 
# FLOW:
# 1. Query BatchUpload by batch_id
# 2. Query all HospitalProcessingResult records for this batch
# 3. Return detailed response with all hospital processing details
# 
# GOES TO:
# - app/database.py → Database queries via get_db()
# - app/models.py::BatchUpload, HospitalProcessingResult → Database models
# ============================================================================
@router.get("/batches/{batch_id}", response_model=BulkUploadResponse)
async def get_batch_details(batch_id: str, db: Session = Depends(get_db)):
    """
    Get detailed results for a specific batch
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
