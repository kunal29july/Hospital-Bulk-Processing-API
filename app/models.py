"""
Database Models Module
======================
This module defines the database schema using SQLAlchemy ORM models.
It contains two main tables for tracking batch uploads and individual hospital processing results.

Tables:
1. batch_uploads: Stores metadata about each CSV upload batch
2. hospital_processing_results: Stores individual hospital processing outcomes

Relationships:
- One batch upload has many hospital processing results (one-to-many)
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


# Enumerations
# ============
# These enums define the possible status values for batches and hospitals

class BatchStatus(str, enum.Enum):
    """
    Batch Processing Status
    
    Tracks the overall status of a batch upload operation.
    
    States:
    - PENDING: Batch created but processing not started
    - PROCESSING: Currently processing hospitals in the batch
    - COMPLETED: All hospitals processed successfully and batch activated
    - FAILED: One or more hospitals failed, or activation failed
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HospitalStatus(str, enum.Enum):
    """
    Individual Hospital Processing Status
    
    Tracks the outcome of processing a single hospital record.
    
    States:
    - CREATED_AND_ACTIVATED: Hospital successfully created and activated
    - FAILED: Hospital creation or validation failed
    """
    CREATED_AND_ACTIVATED = "created_and_activated"
    FAILED = "failed"


# Database Models
# ===============

class BatchUpload(Base):
    """
    Batch Upload Model
    
    Stores information about each CSV file upload and its processing results.
    This is the parent table that tracks the overall batch operation.
    
    Purpose:
    - Track which CSV files were uploaded and when
    - Store aggregate statistics (total, processed, failed counts)
    - Record processing time and final status
    - Link to individual hospital results
    
    Relationships:
    - Has many HospitalProcessingResult records (one-to-many)
    """
    __tablename__ = "batch_uploads"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    """Auto-incrementing primary key"""
    
    # Batch Identification
    batch_id = Column(String, unique=True, index=True, nullable=False)
    """UUID that uniquely identifies this batch (sent to Hospital API)"""
    
    filename = Column(String, nullable=False)
    """Original name of the uploaded CSV file"""
    
    # Processing Statistics
    total_hospitals = Column(Integer, nullable=False)
    """Total number of hospitals in the CSV file"""
    
    processed_hospitals = Column(Integer, default=0)
    """Number of hospitals successfully processed"""
    
    failed_hospitals = Column(Integer, default=0)
    """Number of hospitals that failed processing"""
    
    # Batch State
    batch_activated = Column(Boolean, default=False)
    """Whether the batch was successfully activated in the Hospital API"""
    
    processing_time_seconds = Column(Float, nullable=True)
    """Total time taken to process the entire batch (in seconds)"""
    
    status = Column(Enum(BatchStatus), default=BatchStatus.PENDING)
    """Current status of the batch processing"""
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    """When the batch upload was initiated"""
    
    completed_at = Column(DateTime, nullable=True)
    """When the batch processing completed (success or failure)"""
    
    # Relationships
    hospital_results = relationship(
        "HospitalProcessingResult",
        back_populates="batch_upload",
        cascade="all, delete-orphan"  # Delete results when batch is deleted
    )
    """List of all hospital processing results for this batch"""


class HospitalProcessingResult(Base):
    """
    Hospital Processing Result Model
    
    Stores the outcome of processing each individual hospital in a batch.
    This is the child table that tracks per-hospital results.
    
    Purpose:
    - Record which hospitals succeeded or failed
    - Store hospital details (name, address, phone)
    - Link to the hospital ID in the external API (if successful)
    - Capture error messages for failed hospitals
    
    Relationships:
    - Belongs to one BatchUpload (many-to-one)
    """
    __tablename__ = "hospital_processing_results"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    """Auto-incrementing primary key"""
    
    # Foreign Key to Batch
    batch_upload_id = Column(Integer, ForeignKey("batch_uploads.id"), nullable=False)
    """Links this result to its parent batch upload"""
    
    # Row Information
    row_number = Column(Integer, nullable=False)
    """Row number in the CSV file (for user reference)"""
    
    # Hospital Data from API Response
    hospital_id = Column(Integer, nullable=True)
    """ID assigned by the Hospital API (null if creation failed)"""
    
    # Hospital Details from CSV
    name = Column(String, nullable=False)
    """Hospital name from CSV"""
    
    address = Column(String, nullable=False)
    """Hospital address from CSV"""
    
    phone = Column(String, nullable=True)
    """Hospital phone number from CSV (optional field)"""
    
    # Processing Outcome
    status = Column(Enum(HospitalStatus), nullable=False)
    """Whether this hospital was successfully processed"""
    
    error_message = Column(String, nullable=True)
    """Error message if processing failed (null if successful)"""
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    """When this result was recorded"""
    
    # Relationships
    batch_upload = relationship("BatchUpload", back_populates="hospital_results")
    """Reference to the parent batch upload"""
