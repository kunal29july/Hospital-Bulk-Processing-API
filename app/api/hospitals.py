# ============================================================================
# HOSPITALS ROUTER - Bulk Upload Endpoint
# ============================================================================
# This router handles hospital bulk upload operations
# 
# ENDPOINTS:
# - POST /hospitals/bulk → bulk_create_hospitals()
# 
# FLOW: Called from app/main.py → Processes CSV → Creates hospitals
# ============================================================================

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
import uuid
import time
from datetime import datetime

from app.database import get_db
from app.models import BatchUpload, HospitalProcessingResult, BatchStatus, HospitalStatus
from app.schemas import BulkUploadResponse, HospitalProcessingDetail, HospitalCreate
from app.services.csv_processor import CSVProcessor
from app.services.hospital_client import HospitalAPIClient
from app.logger import logger

router = APIRouter()


@router.post("/hospitals/bulk", response_model=BulkUploadResponse)
async def bulk_create_hospitals(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Bulk create hospitals from CSV file
    
    CSV Format: name,address,phone (phone is optional)
    Maximum 20 hospitals per upload
    
    FLOW:
    1. Validate CSV → app/services/csv_processor.py
    2. Create batch record → Database
    3. Process each hospital → app/services/hospital_client.py
    4. Activate batch if all succeed → External API
    5. Return results
    """
    start_time = time.time()
    
    logger.info("=" * 80)
    logger.info("Starting bulk hospital upload process")
    logger.info(f"File: {file.filename}")
    
    # Step 1: Validate and parse CSV
    # FLOW → app/services/csv_processor.py::validate_and_parse_csv()
    logger.info("Step 1: Validating and parsing CSV file...")
    csv_processor = CSVProcessor()
    rows, filename = await csv_processor.validate_and_parse_csv(file)
    logger.info(f"CSV validated successfully: {len(rows)} hospitals found")
    
    # Step 2: Generate unique batch ID
    logger.info("Step 2: Generating unique batch ID...")
    batch_id = str(uuid.uuid4())
    logger.info(f"Batch ID generated: {batch_id}")
    
    # Step 3: Create batch upload record
    # FLOW → app/models.py::BatchUpload model → Database
    logger.info("Step 3: Creating batch record in database...")
    batch_upload = BatchUpload(
        batch_id=batch_id,
        filename=filename,
        total_hospitals=len(rows),
        status=BatchStatus.PROCESSING
    )
    db.add(batch_upload)
    db.commit()
    db.refresh(batch_upload)
    logger.info(f"Batch record created with ID: {batch_upload.id}")
    
    # Step 4: Warm up external API (prevents cold start timeout on first hospital)
    logger.info("Step 4: Warming up external API...")
    hospital_client = HospitalAPIClient()
    await hospital_client.warmup_api()
    
    # Step 5: Process each hospital
    logger.info(f"Step 5: Processing {len(rows)} hospitals...")
    # FLOW → app/services/hospital_client.py for API calls
    processing_results = []
    processed_count = 0
    failed_count = 0
    
    for idx, row in enumerate(rows, start=1):
        logger.info(f"  Processing hospital {idx}/{len(rows)}: {row.get('name', 'Unknown')}")
        
        # Validate hospital data
        # FLOW → app/services/csv_processor.py::validate_hospital_data()
        is_valid, error_msg = csv_processor.validate_hospital_data(row)
        
        if not is_valid:
            logger.warning(f"  Validation failed for row {idx}: {error_msg}")
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
        logger.info(f"  Calling external API to create hospital...")
        success, hospital_response, error_message = await hospital_client.create_hospital(hospital_data)
        
        if success:
            logger.info(f"  Hospital created successfully with ID: {hospital_response.id}")
            # Record success
            result = HospitalProcessingResult(
                batch_upload_id=batch_upload.id,
                row_number=idx,
                hospital_id=hospital_response.id,
                name=hospital_response.name,
                address=hospital_response.address,
                phone=hospital_response.phone,
                status=HospitalStatus.CREATED_AND_ACTIVATED,
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
            logger.error(f"  Failed to create hospital: {error_message}")
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
    
    # Step 6: Activate batch if all succeeded
    logger.info(f"Step 6: Processing complete - {processed_count} succeeded, {failed_count} failed")
    batch_activated = False
    
    if failed_count == 0:
        logger.info("All hospitals created successfully! Activating batch...")
        # All hospitals created successfully, activate the batch
        # FLOW → app/services/hospital_client.py::activate_batch() → External API
        activation_success, activation_error = await hospital_client.activate_batch(batch_id)
        
        if activation_success:
            logger.info("Batch activated successfully!")
            batch_activated = True
            batch_upload.status = BatchStatus.COMPLETED
        else:
            logger.error(f"Batch activation failed: {activation_error}")
            # Activation failed, mark batch as failed
            batch_upload.status = BatchStatus.FAILED
    else:
        logger.warning(f"Skipping batch activation due to {failed_count} failed hospitals")
        # Some hospitals failed, don't activate
        batch_upload.status = BatchStatus.FAILED
    
    # Step 7: Update batch upload record and commit with retry logic
    logger.info("Step 7: Updating batch record with final results...")
    batch_upload.processed_hospitals = processed_count
    batch_upload.failed_hospitals = failed_count
    batch_upload.batch_activated = batch_activated
    batch_upload.processing_time_seconds = time.time() - start_time
    batch_upload.completed_at = datetime.utcnow()
    
    # Commit with retry logic for database locks
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db.commit()
            logger.info("Batch record updated successfully")
            break
        except OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(1)  # Wait 1 second before retry
                db.rollback()  # Rollback the failed transaction
            else:
                logger.error(f"Failed to commit after {max_retries} attempts: {e}")
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Database is currently busy. Please try again in a moment."
                )
    
    # Step 8: Return response
    processing_time = round(time.time() - start_time, 2)
    logger.info(f"Bulk upload complete! Processing time: {processing_time}s")
    logger.info("=" * 80)
    
    return BulkUploadResponse(
        batch_id=batch_id,
        total_hospitals=len(rows),
        processed_hospitals=processed_count,
        failed_hospitals=failed_count,
        processing_time_seconds=round(time.time() - start_time, 2),
        batch_activated=batch_activated,
        hospitals=processing_results
    )
