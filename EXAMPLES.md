# Hospital Bulk Processing API - Complete Examples Guide

## 📋 Table of Contents
1. [Quick Start Example](#quick-start-example)
2. [CSV File Examples](#csv-file-examples)
3. [API Request Examples](#api-request-examples)
4. [Response Examples](#response-examples)
5. [Error Examples](#error-examples)
6. [Testing Workflow](#testing-workflow)
7. [Real-World Scenarios](#real-world-scenarios)

---

## 🚀 Quick Start Example

### Step 1: Start the Server
```bash
# Navigate to project directory
cd hospital-bulk-processor

# Start the development server
uvicorn app.main:app --reload
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Open Swagger UI
Open your browser and go to: `http://127.0.0.1:8000/docs`

### Step 3: Upload a CSV File
1. Click on **POST /hospitals/bulk**
2. Click **"Try it out"**
3. Click **"Choose File"** and select `sample_hospitals.csv`
4. Click **"Execute"**

### Step 4: View Results
You'll see a response with all hospital details and processing status!

---

## 📄 CSV File Examples

### Example 1: Valid CSV with All Fields
**Filename**: `hospitals_complete.csv`

```csv
name,address,phone
City General Hospital,123 Main Street,555-0101
St. Mary's Medical Center,456 Oak Avenue,555-0102
Memorial Hospital,789 Pine Road,555-0103
Community Health Center,321 Elm Street,555-0104
Regional Medical Center,654 Maple Drive,555-0105
```

**What happens**: All 5 hospitals will be created and activated successfully.

---

### Example 2: Valid CSV without Phone Numbers
**Filename**: `hospitals_no_phone.csv`

```csv
name,address
Downtown Clinic,100 First Street
Suburban Hospital,200 Second Avenue
Rural Health Center,300 Third Road
```

**What happens**: All 3 hospitals created successfully (phone is optional).

---

### Example 3: Maximum Allowed (20 Hospitals)
**Filename**: `hospitals_max.csv`

```csv
name,address,phone
Hospital 1,Address 1,555-0001
Hospital 2,Address 2,555-0002
Hospital 3,Address 3,555-0003
Hospital 4,Address 4,555-0004
Hospital 5,Address 5,555-0005
Hospital 6,Address 6,555-0006
Hospital 7,Address 7,555-0007
Hospital 8,Address 8,555-0008
Hospital 9,Address 9,555-0009
Hospital 10,Address 10,555-0010
Hospital 11,Address 11,555-0011
Hospital 12,Address 12,555-0012
Hospital 13,Address 13,555-0013
Hospital 14,Address 14,555-0014
Hospital 15,Address 15,555-0015
Hospital 16,Address 16,555-0016
Hospital 17,Address 17,555-0017
Hospital 18,Address 18,555-0018
Hospital 19,Address 19,555-0019
Hospital 20,Address 20,555-0020
```

**What happens**: All 20 hospitals processed (this is the maximum allowed).

---

### Example 4: Invalid CSV - Too Many Rows
**Filename**: `hospitals_too_many.csv`

```csv
name,address,phone
Hospital 1,Address 1,555-0001
Hospital 2,Address 2,555-0002
...
Hospital 21,Address 21,555-0021
```

**What happens**: ❌ Error - "CSV file contains 21 rows, but maximum allowed is 20"

---

### Example 5: Invalid CSV - Missing Required Header
**Filename**: `hospitals_missing_header.csv`

```csv
name,phone
City Hospital,555-1234
General Hospital,555-5678
```

**What happens**: ❌ Error - "Missing required header: address"

---

### Example 6: Invalid CSV - Empty Required Field
**Filename**: `hospitals_empty_field.csv`

```csv
name,address,phone
City Hospital,123 Main St,555-1234
,456 Oak Ave,555-5678
Memorial Hospital,789 Pine Rd,555-9012
```

**What happens**: ❌ Error - "Row 3: 'name' is required"

---

## 🌐 API Request Examples

### Example 1: Upload CSV using cURL

```bash
curl -X POST "http://localhost:8000/hospitals/bulk" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_hospitals.csv"
```

**Explanation**:
- `-X POST`: HTTP POST method
- `-H "accept: application/json"`: We want JSON response
- `-H "Content-Type: multipart/form-data"`: File upload format
- `-F "file=@sample_hospitals.csv"`: Upload the CSV file

---

### Example 2: Upload CSV using Python

```python
import requests

# Open and upload the CSV file
with open('sample_hospitals.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/hospitals/bulk',
        files=files
    )

# Print the response
print(response.json())
```

**Output**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_hospitals": 5,
  "processed_hospitals": 5,
  "failed_hospitals": 0,
  "processing_time_seconds": 2.45,
  "batch_activated": true,
  "hospitals": [...]
}
```

---

### Example 3: List All Batches

```bash
curl -X GET "http://localhost:8000/batches"
```

**Response**:
```json
[
  {
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "hospitals.csv",
    "total_hospitals": 5,
    "processed_hospitals": 5,
    "failed_hospitals": 0,
    "batch_activated": true,
    "status": "completed",
    "created_at": "2025-12-14T10:30:00Z",
    "completed_at": "2025-12-14T10:30:05Z"
  },
  {
    "batch_id": "660e8400-e29b-41d4-a716-446655440001",
    "filename": "test.csv",
    "total_hospitals": 3,
    "processed_hospitals": 2,
    "failed_hospitals": 1,
    "batch_activated": false,
    "status": "failed",
    "created_at": "2025-12-14T11:00:00Z",
    "completed_at": "2025-12-14T11:00:03Z"
  }
]
```

---

### Example 4: Get Specific Batch Details

```bash
curl -X GET "http://localhost:8000/batches/550e8400-e29b-41d4-a716-446655440000"
```

**Response**: Same format as bulk upload response with all hospital details.

---

### Example 5: Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Response**:
```json
{
  "status": "healthy"
}
```

---

## 📊 Response Examples

### Example 1: Successful Upload (All Hospitals Created)

**Request**: Upload CSV with 5 hospitals

**Response**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_hospitals": 5,
  "processed_hospitals": 5,
  "failed_hospitals": 0,
  "processing_time_seconds": 2.45,
  "batch_activated": true,
  "hospitals": [
    {
      "row": 1,
      "hospital_id": 101,
      "name": "City General Hospital",
      "status": "created_and_activated",
      "error_message": null
    },
    {
      "row": 2,
      "hospital_id": 102,
      "name": "St. Mary's Medical Center",
      "status": "created_and_activated",
      "error_message": null
    },
    {
      "row": 3,
      "hospital_id": 103,
      "name": "Memorial Hospital",
      "status": "created_and_activated",
      "error_message": null
    },
    {
      "row": 4,
      "hospital_id": 104,
      "name": "Community Health Center",
      "status": "created_and_activated",
      "error_message": null
    },
    {
      "row": 5,
      "hospital_id": 105,
      "name": "Regional Medical Center",
      "status": "created_and_activated",
      "error_message": null
    }
  ]
}
```

**Interpretation**:
- ✅ All 5 hospitals created successfully
- ✅ Batch was activated
- ✅ Processing took 2.45 seconds
- ✅ Each hospital has an ID from the Hospital API

---

### Example 2: Partial Failure (Some Hospitals Failed)

**Request**: Upload CSV where one hospital has invalid data

**Response**:
```json
{
  "batch_id": "660e8400-e29b-41d4-a716-446655440001",
  "total_hospitals": 3,
  "processed_hospitals": 2,
  "failed_hospitals": 1,
  "processing_time_seconds": 1.82,
  "batch_activated": false,
  "hospitals": [
    {
      "row": 1,
      "hospital_id": 106,
      "name": "Downtown Clinic",
      "status": "created_and_activated",
      "error_message": null
    },
    {
      "row": 2,
      "hospital_id": null,
      "name": "A".repeat(201),
      "status": "failed",
      "error_message": "Hospital name too long (max 200 characters)"
    },
    {
      "row": 3,
      "hospital_id": 107,
      "name": "Suburban Hospital",
      "status": "created_and_activated",
      "error_message": null
    }
  ]
}
```

**Interpretation**:
- ⚠️ 2 hospitals created successfully
- ❌ 1 hospital failed (name too long)
- ❌ Batch was NOT activated (because of the failure)
- ℹ️ Successful hospitals are created but remain inactive

---

## ❌ Error Examples

### Error 1: Invalid File Format

**Request**: Upload a .txt file instead of .csv

**Response** (400 Bad Request):
```json
{
  "detail": "File must be a CSV file"
}
```

---

### Error 2: Missing Required Header

**Request**: Upload CSV without 'address' column

**Response** (400 Bad Request):
```json
{
  "detail": "Missing required header: address"
}
```

---

### Error 3: Too Many Rows

**Request**: Upload CSV with 25 hospitals

**Response** (400 Bad Request):
```json
{
  "detail": "CSV file contains 25 rows, but maximum allowed is 20"
}
```

---

### Error 4: Empty Required Field

**Request**: Upload CSV with empty name field

**Response** (400 Bad Request):
```json
{
  "detail": "Row 3: 'name' is required"
}
```

---

### Error 5: Batch Not Found

**Request**: GET /batches/invalid-uuid

**Response** (404 Not Found):
```json
{
  "detail": "Batch not found"
}
```

---

## 🧪 Testing Workflow

### Complete Testing Scenario

#### Step 1: Prepare Test CSV
Create `test_hospitals.csv`:
```csv
name,address,phone
Test Hospital 1,100 Test St,555-0001
Test Hospital 2,200 Test Ave,555-0002
Test Hospital 3,300 Test Rd,555-0003
```

#### Step 2: Upload the CSV
```bash
curl -X POST "http://localhost:8000/hospitals/bulk" \
  -F "file=@test_hospitals.csv" \
  > response.json
```

#### Step 3: Check the Response
```bash
cat response.json | python -m json.tool
```

**Expected Output**:
```json
{
  "batch_id": "abc123...",
  "total_hospitals": 3,
  "processed_hospitals": 3,
  "failed_hospitals": 0,
  "batch_activated": true,
  ...
}
```

#### Step 4: Verify in Database
The SQLite database (`hospital_bulk.db`) now contains:
- 1 record in `batch_uploads` table
- 3 records in `hospital_processing_results` table

#### Step 5: List All Batches
```bash
curl -X GET "http://localhost:8000/batches"
```

You should see your batch in the list!

#### Step 6: Get Batch Details
```bash
curl -X GET "http://localhost:8000/batches/abc123..."
```

You'll see the same detailed response as the upload.

---

## 🌍 Real-World Scenarios

### Scenario 1: Hospital Chain Onboarding

**Situation**: A hospital chain wants to add 15 new locations to the system.

**Solution**:
1. Create CSV with all 15 hospitals
2. Upload via API
3. All hospitals created and activated in one batch
4. Takes ~7-8 seconds total

**CSV Example**:
```csv
name,address,phone
HealthCare Plus - Downtown,100 Main St,555-1001
HealthCare Plus - Uptown,200 Oak Ave,555-1002
HealthCare Plus - Westside,300 Pine Rd,555-1003
...
```

---

### Scenario 2: Data Migration

**Situation**: Migrating hospital data from old system to new system.

**Solution**:
1. Export hospitals from old system to CSV
2. Split into batches of 20 (if more than 20)
3. Upload each batch
4. Track batch IDs for verification

**Process**:
```bash
# Upload batch 1
curl -X POST "http://localhost:8000/hospitals/bulk" -F "file=@batch1.csv"

# Upload batch 2
curl -X POST "http://localhost:8000/hospitals/bulk" -F "file=@batch2.csv"

# Verify all batches
curl -X GET "http://localhost:8000/batches"
```

---

### Scenario 3: Testing with Invalid Data

**Situation**: QA team wants to test error handling.

**Test Cases**:

**Test 1**: Missing required field
```csv
name,address,phone
Valid Hospital,123 Main St,555-0001
,456 Oak Ave,555-0002
```
**Expected**: Error on row 3

**Test 2**: Too many hospitals
```csv
name,address,phone
Hospital 1,Address 1,555-0001
...
Hospital 21,Address 21,555-0021
```
**Expected**: Error - exceeds maximum

**Test 3**: Invalid file type
Upload a .txt file
**Expected**: Error - must be CSV

---

### Scenario 4: Monitoring and Auditing

**Situation**: Admin wants to review all uploads from today.

**Solution**:
```bash
# Get all batches
curl -X GET "http://localhost:8000/batches" > all_batches.json

# Filter by date (using jq)
cat all_batches.json | jq '.[] | select(.created_at | startswith("2025-12-14"))'
```

**Output**: All batches created today with their status.

---

### Scenario 5: Retry Failed Upload

**Situation**: A batch failed due to network issues. Need to retry.

**Solution**:
1. Check which hospitals failed:
```bash
curl -X GET "http://localhost:8000/batches/failed-batch-id"
```

2. Create new CSV with only failed hospitals
3. Upload again:
```bash
curl -X POST "http://localhost:8000/hospitals/bulk" -F "file=@retry.csv"
```

---

## 📝 Summary

This examples guide covers:

✅ **Quick Start**: Get up and running in minutes  
✅ **CSV Examples**: Valid and invalid formats  
✅ **API Requests**: cURL, Python, and more  
✅ **Response Examples**: Success and failure cases  
✅ **Error Examples**: All possible error scenarios  
✅ **Testing Workflow**: Complete testing process  
✅ **Real-World Scenarios**: Practical use cases  

Use these examples to:
- Understand how the API works
- Test different scenarios
- Integrate with your applications
- Train your team
- Debug issues

For more information, see:
- `README.md` - General documentation
- `ARCHITECTURE.md` - System architecture
- `/docs` - Interactive API documentation (Swagger UI)
