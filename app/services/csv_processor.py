# ============================================================================
# CSV PROCESSOR SERVICE - FLOW CONTINUES FROM app/api/endpoints.py
# ============================================================================
# This service handles CSV file validation and parsing for hospital bulk uploads
# 
# CALLED FROM:
# - app/api/endpoints.py::bulk_create_hospitals()
# 
# METHODS:
# 1. validate_and_parse_csv() → Validates CSV format and parses rows
# 2. validate_hospital_data() → Validates individual hospital record data
# 
# FLOW:
# CSV Upload → validate_and_parse_csv() → Returns parsed rows
# Each row → validate_hospital_data() → Returns validation result
# 
# DEPENDENCIES:
# - app.config → Settings (max_csv_rows limit)
# ============================================================================

import csv
import io
from typing import List, Dict, Tuple
from fastapi import UploadFile, HTTPException
from app.config import get_settings
from app.logger import logger

settings = get_settings()


class CSVProcessor:
    """Processor for CSV file validation and parsing"""
    
    REQUIRED_HEADERS = ["name", "address"]
    OPTIONAL_HEADERS = ["phone"]
    ALL_HEADERS = REQUIRED_HEADERS + OPTIONAL_HEADERS
    
    # ========================================================================
    # METHOD 1: validate_and_parse_csv
    # ========================================================================
    # Validates CSV file format and parses all rows
    # 
    # VALIDATION CHECKS:
    # 1. File extension must be .csv
    # 2. File must be UTF-8 encoded
    # 3. Must have required headers: name, address
    # 4. Optional header: phone
    # 5. No unexpected headers allowed
    # 6. Each row must have name and address (required fields)
    # 7. Total rows must not exceed max_csv_rows (from config)
    # 
    # RETURNS TO: app/api/endpoints.py with parsed rows and filename
    # ========================================================================
    @staticmethod
    async def validate_and_parse_csv(file: UploadFile) -> Tuple[List[Dict[str, str]], str]:
        """
        Validate and parse CSV file
        
        Args:
            file: Uploaded CSV file
            
        Returns:
            Tuple of (parsed_rows, filename)
            
        Raises:
            HTTPException: If validation fails
        """
        # Step 1: Check file extension
        logger.info(f"  Checking file extension: {file.filename}")
        if not file.filename.endswith('.csv'):
            logger.error("  Invalid file extension")
            raise HTTPException(
                status_code=400,
                detail="File must be a CSV file"
            )
        logger.info("  File extension valid")
        
        # Step 2: Read and decode file content
        logger.info("  Reading and decoding file content...")
        try:
            content = await file.read()
            content_str = content.decode('utf-8')
            logger.info(f"  File decoded successfully ({len(content)} bytes)")
        except UnicodeDecodeError:
            logger.error("  File encoding error")
            raise HTTPException(
                status_code=400,
                detail="File must be UTF-8 encoded"
            )
        
        # Step 3: Parse CSV using DictReader
        logger.info("  Parsing CSV content...")
        csv_reader = csv.DictReader(io.StringIO(content_str))
        
        # Step 4: Validate headers
        if not csv_reader.fieldnames:
            logger.error("  CSV file has no headers")
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty or has no headers"
            )
        
        headers = [h.strip().lower() for h in csv_reader.fieldnames]
        logger.info(f"  Headers found: {', '.join(headers)}")
        
        # Step 5: Check required headers (name, address)
        logger.info("  Validating required headers...")
        for required_header in CSVProcessor.REQUIRED_HEADERS:
            if required_header not in headers:
                logger.error(f"  Missing required header: {required_header}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required header: {required_header}"
                )
        logger.info("  All required headers present")
        
        # Step 6: Check for unexpected headers
        for header in headers:
            if header not in CSVProcessor.ALL_HEADERS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unexpected header: {header}. Allowed headers are: {', '.join(CSVProcessor.ALL_HEADERS)}"
                )
        
        # Step 7: Parse and validate each row
        rows = []
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (1 is header)
            # Normalize keys to lowercase and trim whitespace
            normalized_row = {k.strip().lower(): v.strip() if v else None for k, v in row.items()}
            
            # Ensure phone key exists even if not in CSV
            if 'phone' not in normalized_row:
                normalized_row['phone'] = None
            
            # Validate required fields are not empty
            if not normalized_row.get('name'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Row {row_num}: 'name' is required"
                )
            
            if not normalized_row.get('address'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Row {row_num}: 'address' is required"
                )
            
            rows.append(normalized_row)
        
        # Step 8: Check if file has data rows
        if not rows:
            raise HTTPException(
                status_code=400,
                detail="CSV file contains no data rows"
            )
        
        # Step 9: Check max rows limit (from app/config.py)
        logger.info(f"  Checking row count: {len(rows)} rows (max: {settings.max_csv_rows})")
        if len(rows) > settings.max_csv_rows:
            logger.error(f"  Too many rows: {len(rows)} > {settings.max_csv_rows}")
            raise HTTPException(
                status_code=400,
                detail=f"CSV file contains {len(rows)} rows, but maximum allowed is {settings.max_csv_rows}"
            )
        logger.info(f"  Row count valid: {len(rows)} rows")
        
        # RETURNS TO: app/api/endpoints.py::bulk_create_hospitals()
        return rows, file.filename
    
    # ========================================================================
    # METHOD 2: validate_hospital_data
    # ========================================================================
    # Validates individual hospital record data (field lengths)
    # 
    # VALIDATION CHECKS:
    # 1. Name length ≤ 200 characters
    # 2. Address length ≤ 500 characters
    # 3. Phone length ≤ 20 characters (if provided)
    # 
    # CALLED FROM: app/api/endpoints.py for each parsed row
    # RETURNS TO: app/api/endpoints.py with validation result
    # ========================================================================
    @staticmethod
    def validate_hospital_data(row: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate individual hospital data
        
        Args:
            row: Dictionary containing hospital data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate name length
        if len(row.get('name', '')) > 200:
            return False, "Hospital name too long (max 200 characters)"
        
        # Validate address length
        if len(row.get('address', '')) > 500:
            return False, "Address too long (max 500 characters)"
        
        # Validate phone length (if provided)
        phone = row.get('phone')
        if phone and len(phone) > 20:
            return False, "Phone number too long (max 20 characters)"
        
        # All validations passed
        # RETURNS TO: app/api/endpoints.py::bulk_create_hospitals()
        return True, ""
