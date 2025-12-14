"""
Pydantic Schemas Module
=======================
This module defines Pydantic models for request/response validation and serialization.
Pydantic automatically validates data types and provides clear error messages.

Schema Categories:
1. Hospital API Schemas: For communicating with the Hospital Directory API
2. Response Schemas: For our API responses
3. Internal Schemas: For data transfer between components
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Hospital API Schemas
# ====================
# These schemas match the Hospital Directory API's expected format

class HospitalCreate(BaseModel):
    """
    Schema for Creating a Hospital via External API
    
    This matches the format expected by the Hospital Directory API
    when creating a new hospital record.
    
    Fields:
    - name: Hospital name (required)
    - address: Hospital address (required)
    - phone: Contact phone number (optional)
    - creation_batch_id: UUID linking this hospital to a batch
    """
    name: str
    address: str
    phone: Optional[str] = None
    creation_batch_id: str


class HospitalResponse(BaseModel):
    """
    Schema for Hospital Response from External API
    
    This represents the data structure returned by the Hospital Directory API
    after successfully creating a hospital.
    
    Fields:
    - id: Hospital ID assigned by the API
    - name: Hospital name
    - address: Hospital address
    - phone: Contact phone number
    - creation_batch_id: UUID of the batch this hospital belongs to
    - active: Whether the hospital is active (initially false)
    - created_at: Timestamp when hospital was created
    """
    id: int
    name: str
    address: str
    phone: Optional[str] = None
    creation_batch_id: str
    active: bool
    created_at: datetime


# Response Schemas
# ================
# These schemas define the structure of our API responses

class HospitalProcessingDetail(BaseModel):
    """
    Schema for Individual Hospital Processing Result
    
    Represents the outcome of processing a single hospital from the CSV.
    This is included in the bulk upload response to show per-hospital results.
    
    Fields:
    - row: Row number in the CSV file (for user reference)
    - hospital_id: ID from Hospital API (null if failed)
    - name: Hospital name from CSV
    - status: "created_and_activated" or "failed"
    - error_message: Error details if failed (null if successful)
    """
    row: int
    hospital_id: Optional[int] = None
    name: str
    status: str
    error_message: Optional[str] = None


class BulkUploadResponse(BaseModel):
    """
    Schema for Bulk Upload Response
    
    This is the main response returned after processing a CSV upload.
    It provides comprehensive information about the batch processing results.
    
    Fields:
    - batch_id: UUID identifying this batch
    - total_hospitals: Total number of hospitals in CSV
    - processed_hospitals: Number successfully processed
    - failed_hospitals: Number that failed
    - processing_time_seconds: Time taken to process
    - batch_activated: Whether batch was activated in Hospital API
    - hospitals: List of per-hospital results
    
    Example Response:
    {
        "batch_id": "550e8400-e29b-41d4-a716-446655440000",
        "total_hospitals": 5,
        "processed_hospitals": 5,
        "failed_hospitals": 0,
        "processing_time_seconds": 2.45,
        "batch_activated": true,
        "hospitals": [...]
    }
    """
    batch_id: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    processing_time_seconds: float
    batch_activated: bool
    hospitals: List[HospitalProcessingDetail]


class BatchSummary(BaseModel):
    """
    Schema for Batch Summary
    
    Provides a high-level overview of a batch upload.
    Used when listing all batches or getting batch history.
    
    Fields:
    - batch_id: UUID identifying the batch
    - filename: Original CSV filename
    - total_hospitals: Total hospitals in batch
    - processed_hospitals: Successfully processed count
    - failed_hospitals: Failed count
    - batch_activated: Whether batch was activated
    - status: Current batch status (pending/processing/completed/failed)
    - created_at: When batch was created
    - completed_at: When batch processing finished
    """
    batch_id: str
    filename: str
    total_hospitals: int
    processed_hospitals: int
    failed_hospitals: int
    batch_activated: bool
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration"""
        from_attributes = True  # Allow creating from ORM models


class ErrorResponse(BaseModel):
    """
    Schema for Error Responses
    
    Standard error response format for all API errors.
    FastAPI automatically uses this for HTTPException responses.
    
    Fields:
    - detail: Human-readable error message
    
    Example:
    {
        "detail": "CSV file contains 25 rows, but maximum allowed is 20"
    }
    """
    detail: str
