# ============================================================================
# HOSPITAL API CLIENT SERVICE - FLOW CONTINUES FROM app/api/endpoints.py
# ============================================================================
# This service handles all HTTP communication with the external Hospital Directory API
# 
# CALLED FROM:
# - app/api/endpoints.py::bulk_create_hospitals()
# 
# METHODS:
# 1. create_hospital() → POST to external API to create a hospital
# 2. activate_batch() → PATCH to external API to activate all hospitals in batch
# 3. delete_batch() → DELETE to external API to remove batch (cleanup, not currently used)
# 
# FLOW:
# For each valid hospital row:
#   → create_hospital() → External Hospital API → Returns success/failure
# 
# If all hospitals created successfully:
#   → activate_batch() → External Hospital API → Activates all hospitals in batch
# 
# EXTERNAL API ENDPOINTS CALLED:
# - POST {base_url}/hospitals/ → Create single hospital
# - PATCH {base_url}/hospitals/batch/{batch_id}/activate → Activate batch
# - DELETE {base_url}/hospitals/batch/{batch_id} → Delete batch (cleanup)
# 
# DEPENDENCIES:
# - app.config → Settings (hospital_api_base_url)
# - app.schemas → HospitalCreate, HospitalResponse (Pydantic models)
# - httpx → Async HTTP client library
# ============================================================================

import httpx
import asyncio
from typing import Optional, Dict, Any
from app.config import get_settings
from app.schemas import HospitalCreate, HospitalResponse
from app.logger import logger

# Load application settings
settings = get_settings()


class HospitalAPIClient:
    """
    HTTP Client for Hospital Directory API
    
    This class encapsulates all communication with the external Hospital Directory API.
    It provides methods for creating hospitals, activating batches, and cleanup operations.
    
    Design Pattern: This is a service class that abstracts API communication details
    from the business logic in our endpoints.
    
    Attributes:
        base_url: Base URL of the Hospital Directory API
        timeout: Request timeout in seconds (prevents hanging requests)
    """
    
    def __init__(self):
        """
        Initialize the Hospital API Client
        
        Sets up the base URL and timeout from application configuration.
        """
        self.base_url = settings.hospital_api_base_url
        self.timeout = 90.0  # 90 seconds timeout to handle cold starts
        self.max_retries = 2  # Number of retries for failed requests
        self.retry_delay = 5  # Seconds to wait between retries
        # Disable SSL verification for development (external API uses self-signed cert)
        self.verify_ssl = False
    
    # ========================================================================
    # METHOD 0: warmup_api (NEW)
    # ========================================================================
    # Sends a warmup request to wake up the external API (handles cold starts)
    # 
    # FLOW:
    # 1. Called from app/api/endpoints.py BEFORE processing hospitals
    # 2. Send GET request to external API root endpoint
    # 3. This wakes up the service if it's in cold start
    # 4. Subsequent hospital creation requests will be faster
    # 
    # EXTERNAL API CALL:
    # GET {base_url}/
    # ========================================================================
    async def warmup_api(self) -> bool:
        """
        Warm Up the External API
        
        Sends a simple GET request to the external API to wake it up
        if it's in a cold start state (common on free-tier hosting).
        This prevents the first hospital creation from timing out.
        
        Returns:
            bool: True if warmup successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=self.verify_ssl) as client:
                logger.info(f"  Warming up external API: GET {self.base_url}/")
                response = await client.get(f"{self.base_url}/")
                
                if response.status_code == 200:
                    logger.info(f"  API warmup successful (status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"  API warmup returned status {response.status_code}")
                    return True  # Still consider it successful - API is responding
                    
        except Exception as e:
            logger.warning(f"  API warmup failed: {str(e)} - continuing anyway")
            return False  # Don't fail the entire process if warmup fails
    
    # ========================================================================
    # METHOD 1: create_hospital
    # ========================================================================
    # Creates a single hospital via external Hospital Directory API
    # 
    # FLOW:
    # 1. Receive HospitalCreate data from app/api/endpoints.py
    # 2. Send POST request to external API: {base_url}/hospitals/
    # 3. Parse response if successful (status 200/201)
    # 4. Handle errors (timeout, network, API errors)
    # 
    # EXTERNAL API CALL:
    # POST {base_url}/hospitals/
    # Body: {"name": "...", "address": "...", "phone": "...", "creation_batch_id": "..."}
    # 
    # RETURNS TO: app/api/endpoints.py::bulk_create_hospitals()
    # ========================================================================
    async def create_hospital(
        self, 
        hospital_data: HospitalCreate
    ) -> tuple[bool, Optional[HospitalResponse], Optional[str]]:
        """
        Create a Hospital via the External API with Retry Logic
        
        This method sends a POST request to create a single hospital record.
        It includes retry logic to handle transient failures and cold starts.
        
        Process:
        1. Attempt to create hospital
        2. If fails, retry up to max_retries times with delays
        3. Return success or final failure
        
        Args:
            hospital_data: Hospital information to create (name, address, phone, batch_id)
        
        Returns:
            tuple containing:
            - success (bool): True if hospital was created successfully
            - hospital_response (HospitalResponse | None): Hospital data from API if successful
            - error_message (str | None): Error description if failed
        """
        last_error = None
        
        # Retry loop: attempt creation up to (1 + max_retries) times
        for attempt in range(1 + self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
                    # Log attempt number
                    if attempt == 0:
                        logger.info(f"    POST {self.base_url}/hospitals/")
                    else:
                        logger.info(f"    Retry {attempt}/{self.max_retries}: POST {self.base_url}/hospitals/")
                    
                    # Send POST request to external Hospital API
                    response = await client.post(
                        f"{self.base_url}/hospitals/",
                        json=hospital_data.model_dump()
                    )
                    
                    # Check if request was successful
                    if response.status_code == 200 or response.status_code == 201:
                        hospital_response = HospitalResponse(**response.json())
                        logger.info(f"    Response: {response.status_code} - Hospital ID: {hospital_response.id}")
                        return True, hospital_response, None
                    else:
                        # API returned an error - may be retryable
                        last_error = f"API returned status {response.status_code}: {response.text}"
                        logger.warning(f"    Response: {response.status_code} - {last_error}")
                        
                        # Don't retry on 4xx errors (client errors - won't succeed on retry)
                        if 400 <= response.status_code < 500:
                            logger.error(f"    Client error - not retrying")
                            return False, None, last_error
                        
            except httpx.TimeoutException:
                last_error = "Request timeout"
                logger.warning(f"    Request timeout (>{self.timeout}s)")
                
            except httpx.RequestError as e:
                last_error = f"Request error: {str(e)}"
                logger.warning(f"    Request error: {str(e)}")
                
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.warning(f"    Unexpected error: {str(e)}")
            
            # If we haven't returned yet, the request failed
            # Wait before retrying (unless this was the last attempt)
            if attempt < self.max_retries:
                logger.info(f"    Waiting {self.retry_delay}s before retry...")
                await asyncio.sleep(self.retry_delay)
        
        # All retries exhausted
        logger.error(f"    Failed after {1 + self.max_retries} attempts: {last_error}")
        return False, None, last_error
    
    # ========================================================================
    # METHOD 2: activate_batch
    # ========================================================================
    # Activates all hospitals in a batch via external Hospital Directory API
    # 
    # FLOW:
    # 1. Called from app/api/endpoints.py ONLY if all hospitals created successfully
    # 2. Send PATCH request to external API: {base_url}/hospitals/batch/{batch_id}/activate
    # 3. External API activates all hospitals with this batch_id
    # 4. Return success/failure
    # 
    # EXTERNAL API CALL:
    # PATCH {base_url}/hospitals/batch/{batch_id}/activate
    # 
    # IMPORTANT: Only called when failed_count == 0 in endpoints.py
    # 
    # RETURNS TO: app/api/endpoints.py::bulk_create_hospitals()
    # ========================================================================
    async def activate_batch(self, batch_id: str) -> tuple[bool, Optional[str]]:
        """
        Activate All Hospitals in a Batch
        
        This method calls the Hospital API to activate all hospitals that were
        created with the given batch_id. This makes them visible/active in the system.
        
        Important: This should only be called after ALL hospitals in the batch
        have been successfully created. If any hospital failed, don't activate.
        
        Process:
        1. Send PATCH request to activate endpoint
        2. Check response status
        3. Return success/failure
        
        Args:
            batch_id: UUID of the batch to activate
        
        Returns:
            tuple containing:
            - success (bool): True if batch was activated successfully
            - error_message (str | None): Error description if failed
        
        Example:
            success, error = await client.activate_batch("550e8400-...")
            if success:
                print("Batch activated successfully")
            else:
                print(f"Activation failed: {error}")
        """
        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            try:
                # Send PATCH request to external Hospital API to activate batch
                # EXTERNAL API CALL → PATCH {base_url}/hospitals/batch/{batch_id}/activate
                logger.info(f"  PATCH {self.base_url}/hospitals/batch/{batch_id}/activate")
                response = await client.patch(
                    f"{self.base_url}/hospitals/batch/{batch_id}/activate"
                )
                
                # Check if activation was successful
                if response.status_code == 200:
                    logger.info(f"  Response: {response.status_code} - Batch activated")
                    # RETURNS TO: app/api/endpoints.py with success
                    return True, None
                else:
                    # Activation failed
                    error_msg = f"Batch activation failed with status {response.status_code}: {response.text}"
                    logger.error(f"  Response: {response.status_code} - {error_msg}")
                    # RETURNS TO: app/api/endpoints.py with failure
                    return False, error_msg
                    
            except httpx.TimeoutException:
                logger.error("  Batch activation timeout")
                return False, "Batch activation timeout"
            
            except httpx.RequestError as e:
                logger.error(f"  Batch activation request error: {str(e)}")
                return False, f"Batch activation request error: {str(e)}"
            
            except Exception as e:
                logger.error(f"  Batch activation unexpected error: {str(e)}")
                return False, f"Batch activation unexpected error: {str(e)}"
    
    # ========================================================================
    # METHOD 3: delete_batch
    # ========================================================================
    # Deletes all hospitals in a batch via external Hospital Directory API
    # 
    # FLOW:
    # 1. Send DELETE request to external API: {base_url}/hospitals/batch/{batch_id}
    # 2. External API deletes all hospitals with this batch_id
    # 3. Return success/failure
    # 
    # EXTERNAL API CALL:
    # DELETE {base_url}/hospitals/batch/{batch_id}
    # 
    # NOTE: Currently NOT used in main flow (app/api/endpoints.py)
    # Available for future cleanup/retry logic
    # ========================================================================
    async def delete_batch(self, batch_id: str) -> tuple[bool, Optional[str]]:
        """
        Delete All Hospitals in a Batch (Cleanup)
        
        This method deletes all hospitals associated with a batch_id.
        It's used for cleanup when processing fails and we want to remove
        partially created hospitals.
        
        Note: This is currently not used in the main flow, but is available
        for future enhancements (e.g., retry logic, manual cleanup).
        
        Args:
            batch_id: UUID of the batch to delete
        
        Returns:
            tuple containing:
            - success (bool): True if batch was deleted successfully
            - error_message (str | None): Error description if failed
        
        Example:
            success, error = await client.delete_batch("550e8400-...")
            if success:
                print("Batch deleted successfully")
        """
        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_ssl) as client:
            try:
                # Send DELETE request to external Hospital API to remove batch
                # EXTERNAL API CALL → DELETE {base_url}/hospitals/batch/{batch_id}
                response = await client.delete(
                    f"{self.base_url}/hospitals/batch/{batch_id}"
                )
                
                # Check if deletion was successful (200 or 204 No Content)
                if response.status_code == 200 or response.status_code == 204:
                    return True, None
                else:
                    error_msg = f"Batch deletion failed with status {response.status_code}: {response.text}"
                    return False, error_msg
                    
            except Exception as e:
                return False, f"Batch deletion error: {str(e)}"
