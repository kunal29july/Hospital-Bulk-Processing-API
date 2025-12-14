# Hospital Bulk Processing API - Architecture & Flow Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Design](#architecture-design)
3. [Data Flow](#data-flow)
4. [Main Features](#main-features)
5. [Component Details](#component-details)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Error Handling Strategy](#error-handling-strategy)
9. [Technology Stack](#technology-stack)

---

## 🎯 System Overview

### What Does This System Do?

This is a **bulk processing API** that acts as a middleware between users and the Hospital Directory API. Instead of creating hospitals one by one, users can upload a CSV file with multiple hospitals, and our system:

1. ✅ Validates the CSV file
2. ✅ Creates each hospital via the Hospital Directory API
3. ✅ Activates all hospitals as a batch
4. ✅ Stores processing history in a database
5. ✅ Returns detailed results

### Why Do We Need This?

**Problem**: The Hospital Directory API only accepts one hospital at a time.  
**Solution**: Our system provides bulk upload capability, making it easy to add 20 hospitals at once.

---

## 🏗️ Architecture Design

### High-Level Architecture

```
┌─────────────┐
│    User     │
│  (Browser)  │
└──────┬──────┘
       │ Uploads CSV
       ↓
┌─────────────────────────────────────────────────────────┐
│           Hospital Bulk Processing API                  │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   FastAPI  │→ │ CSV Processor│→ │ Hospital Client│ │
│  │  Endpoints │  │   Service    │  │    Service     │ │
│  └────────────┘  └──────────────┘  └────────┬───────┘ │
│         ↓                                     │         │
│  ┌────────────┐                              │         │
│  │  SQLite DB │                              │         │
│  │  (History) │                              │         │
│  └────────────┘                              │         │
└──────────────────────────────────────────────┼─────────┘
                                               │
                                               ↓ HTTP Calls
                                    ┌──────────────────────┐
                                    │ Hospital Directory   │
                                    │       API            │
                                    │ (External Service)   │
                                    └──────────────────────┘
```

### Layered Architecture

Our system follows a **3-tier architecture**:

```
┌─────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (API Layer)                     │
│  - FastAPI Endpoints                                │
│  - Request/Response Handling                        │
│  - Input Validation                                 │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  BUSINESS LOGIC LAYER (Service Layer)               │
│  - CSV Processing Service                           │
│  - Hospital API Client Service                      │
│  - Batch Processing Logic                           │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  DATA LAYER (Persistence Layer)                     │
│  - SQLAlchemy ORM                                   │
│  - SQLite Database                                  │
│  - Models & Schemas                                 │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

### Complete Request Flow (Step by Step)

Let's trace what happens when a user uploads a CSV file:

```
1. USER UPLOADS CSV
   ↓
2. FastAPI receives multipart/form-data
   ↓
3. CSV Processor validates file
   - Check file extension (.csv)
   - Check file encoding (UTF-8)
   - Validate headers (name, address, phone)
   - Check row count (max 20)
   - Validate required fields
   ↓
4. Generate Batch ID (UUID)
   ↓
5. Create BatchUpload record in database
   - Status: PROCESSING
   - Store filename, total count
   ↓
6. FOR EACH HOSPITAL IN CSV:
   ├─ Validate hospital data
   ├─ Call Hospital API to create hospital
   │  └─ Hospital created with batch_id (inactive)
   ├─ Store result in database
   │  └─ Success: hospital_id, status
   │  └─ Failure: error_message
   └─ Continue to next hospital
   ↓
7. CHECK RESULTS:
   ├─ All succeeded? → Call Hospital API to activate batch
   │                   └─ All hospitals become active
   └─ Any failed? → Don't activate batch
   ↓
8. Update BatchUpload record
   - Status: COMPLETED or FAILED
   - Processing time
   - Final counts
   ↓
9. Return response to user
   - Batch ID
   - Success/failure counts
   - Per-hospital details
```

### Visual Flow Diagram

```
┌──────────────┐
│ CSV Upload   │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ VALIDATION PHASE                         │
│ • File format check                      │
│ • Header validation                      │
│ • Row count check                        │
│ • Data validation                        │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ INITIALIZATION PHASE                     │
│ • Generate UUID batch_id                 │
│ • Create database record                 │
│ • Set status = PROCESSING                │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ PROCESSING PHASE (Loop)                  │
│ ┌────────────────────────────────────┐   │
│ │ For each hospital:                 │   │
│ │ 1. Validate data                   │   │
│ │ 2. Call Hospital API               │   │
│ │ 3. Store result                    │   │
│ │ 4. Continue or stop on error       │   │
│ └────────────────────────────────────┘   │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ ACTIVATION PHASE                         │
│ • Check if all succeeded                 │
│ • If yes: Activate batch                 │
│ • If no: Skip activation                 │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ FINALIZATION PHASE                       │
│ • Update database record                 │
│ • Calculate processing time              │
│ • Set final status                       │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────┐
│ Return Result│
└──────────────┘
```

---

## ⭐ Main Features

### 1. Bulk CSV Upload
**What**: Upload a CSV file with up to 20 hospitals  
**How**: POST /hospitals/bulk with multipart/form-data  
**Why**: Saves time compared to creating hospitals one by one

**CSV Format**:
```csv
name,address,phone
City Hospital,123 Main St,555-1234
General Hospital,456 Oak Ave,555-5678
```

### 2. Comprehensive Validation
**What**: Multi-level validation before processing  
**Levels**:
- File format validation (must be .csv)
- Header validation (name, address required; phone optional)
- Row count validation (max 20 hospitals)
- Data validation (field lengths, required fields)

**Why**: Catch errors early before making API calls

### 3. Batch Processing with Tracking
**What**: Process all hospitals and track each one  
**How**: 
- Generate unique UUID for the batch
- Create each hospital with the batch_id
- Store success/failure for each hospital
- Link all hospitals to the same batch

**Why**: Easy to track which hospitals belong together

### 4. Automatic Batch Activation
**What**: Activate all hospitals at once if all succeed  
**How**: 
- Only activate if ALL hospitals created successfully
- Call PATCH /hospitals/batch/{batch_id}/activate
- All hospitals become active simultaneously

**Why**: Ensures data consistency (all or nothing)

### 5. Detailed Result Reporting
**What**: Comprehensive response with per-hospital details  
**Includes**:
- Batch ID
- Total/processed/failed counts
- Processing time
- Activation status
- Per-hospital results with row numbers

**Why**: User knows exactly what happened

### 6. Processing History
**What**: Store all batch uploads in database  
**Includes**:
- Batch metadata (filename, counts, status)
- Individual hospital results
- Timestamps and processing time

**Why**: Audit trail and ability to review past uploads

### 7. Bonus Features
- **GET /batches**: List all batch uploads
- **GET /batches/{batch_id}**: Get detailed results for a specific batch
- **Health Check**: GET /health endpoint
- **Auto-generated API docs**: Swagger UI at /docs

---

## 🔧 Component Details

### 1. Configuration Module (`app/config.py`)
**Purpose**: Centralized configuration management  
**Key Features**:
- Loads from environment variables
- Provides default values
- Singleton pattern (cached)

**Settings**:
- `HOSPITAL_API_BASE_URL`: External API URL
- `DATABASE_URL`: SQLite connection string
- `MAX_CSV_ROWS`: Maximum hospitals per upload

### 2. Database Module (`app/database.py`)
**Purpose**: Database connection and session management  
**Key Components**:
- `engine`: Database connection pool
- `SessionLocal`: Session factory
- `Base`: Base class for models
- `get_db()`: Dependency injection for routes
- `init_db()`: Create tables on startup

### 3. Models Module (`app/models.py`)
**Purpose**: Define database schema  
**Tables**:
1. **BatchUpload**: Stores batch metadata
   - batch_id, filename, counts, status, timestamps
2. **HospitalProcessingResult**: Stores per-hospital results
   - row_number, hospital_id, name, address, phone, status, error

**Relationships**: One batch → Many results

### 4. Schemas Module (`app/schemas.py`)
**Purpose**: Request/response validation with Pydantic  
**Key Schemas**:
- `HospitalCreate`: For creating hospitals
- `HospitalResponse`: From Hospital API
- `BulkUploadResponse`: Our main response
- `BatchSummary`: For listing batches

### 5. CSV Processor Service (`app/services/csv_processor.py`)
**Purpose**: Validate and parse CSV files  
**Key Methods**:
- `validate_and_parse_csv()`: Main validation logic
- `validate_hospital_data()`: Per-hospital validation

**Validations**:
- File extension, encoding, headers
- Row count, required fields
- Field length limits

### 6. Hospital API Client (`app/services/hospital_client.py`)
**Purpose**: Communicate with Hospital Directory API  
**Key Methods**:
- `create_hospital()`: POST /hospitals/
- `activate_batch()`: PATCH /hospitals/batch/{id}/activate
- `delete_batch()`: DELETE /hospitals/batch/{id}

**Features**:
- Async HTTP requests
- Timeout handling
- Error handling

### 7. API Endpoints (`app/api/endpoints.py`)
**Purpose**: Define API routes  
**Endpoints**:
- `POST /hospitals/bulk`: Main bulk upload
- `GET /batches`: List all batches
- `GET /batches/{batch_id}`: Get batch details

### 8. Main Application (`app/main.py`)
**Purpose**: FastAPI application setup  
**Features**:
- App initialization
- CORS middleware
- Lifespan events (startup/shutdown)
- Route registration

---

## 💾 Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────┐
│           BatchUpload                   │
├─────────────────────────────────────────┤
│ PK  id                                  │
│     batch_id (UUID, unique)             │
│     filename                            │
│     total_hospitals                     │
│     processed_hospitals                 │
│     failed_hospitals                    │
│     batch_activated                     │
│     processing_time_seconds             │
│     status (enum)                       │
│     created_at                          │
│     completed_at                        │
└──────────────┬──────────────────────────┘
               │ 1
               │
               │ has many
               │
               │ N
┌──────────────┴──────────────────────────┐
│    HospitalProcessingResult             │
├─────────────────────────────────────────┤
│ PK  id                                  │
│ FK  batch_upload_id                     │
│     row_number                          │
│     hospital_id (from API)              │
│     name                                │
│     address                             │
│     phone                               │
│     status (enum)                       │
│     error_message                       │
│     created_at                          │
└─────────────────────────────────────────┘
```

### Sample Data

**BatchUpload Table**:
```
id | batch_id                             | filename        | total | processed | failed | activated | status
1  | 550e8400-e29b-41d4-a716-446655440000 | hospitals.csv   | 5     | 5         | 0      | true      | completed
2  | 660e8400-e29b-41d4-a716-446655440001 | test.csv        | 3     | 2         | 1      | false     | failed
```

**HospitalProcessingResult Table**:
```
id | batch_id | row | hospital_id | name            | status                | error
1  | 1        | 1   | 101         | City Hospital   | created_and_activated | null
2  | 1        | 2   | 102         | General Hosp    | created_and_activated | null
3  | 2        | 1   | 103         | Memorial Hosp   | created_and_activated | null
4  | 2        | 2   | null        | Invalid Hosp    | failed                | Name too long
```

---

## 🌐 API Endpoints

### 1. POST /hospitals/bulk
**Purpose**: Upload CSV and process hospitals  
**Request**: multipart/form-data with CSV file  
**Response**: BulkUploadResponse with detailed results

**Example Request**:
```bash
curl -X POST "http://localhost:8000/hospitals/bulk" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@hospitals.csv"
```

**Example Response**:
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
      "name": "City Hospital",
      "status": "created_and_activated",
      "error_message": null
    }
  ]
}
```

### 2. GET /batches
**Purpose**: List all batch uploads  
**Response**: Array of BatchSummary

### 3. GET /batches/{batch_id}
**Purpose**: Get detailed results for a specific batch  
**Response**: BulkUploadResponse

### 4. GET /health
**Purpose**: Health check  
**Response**: `{"status": "healthy"}`

### 5. GET /
**Purpose**: Root endpoint with API info  
**Response**: API metadata and endpoint list

---

## 🛡️ Error Handling Strategy

### Validation Errors (400 Bad Request)
- Invalid CSV format
- Missing required headers
- Too many rows (> 20)
- Empty required fields
- Field length violations

### Processing Errors
- **Individual Hospital Failure**: 
  - Record error in database
  - Continue processing other hospitals
  - Don't activate batch
  
- **API Communication Errors**:
  - Timeout: Retry not implemented (future enhancement)
  - Network error: Record error and continue
  - API error: Record error message

### Database Errors
- Transaction rollback on critical errors
- Graceful error messages to user

---

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework
  - Async support
  - Auto-generated docs
  - Type validation

### Database
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Lightweight database (development)
  - Easy setup, no server needed
  - File-based storage

### Data Validation
- **Pydantic**: Data validation using Python type hints
  - Automatic validation
  - Clear error messages

### HTTP Client
- **httpx**: Async HTTP client
  - Better than requests for async
  - Timeout support

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support

### Deployment
- **Uvicorn**: ASGI server
- **Render**: Cloud platform (configured)

---

## 📊 Performance Considerations

### Current Implementation
- **Sequential Processing**: Hospitals processed one by one
- **Synchronous API Calls**: Wait for each hospital before next
- **Processing Time**: ~0.5 seconds per hospital

### Why Sequential?
1. Simpler error handling
2. Easier to track progress
3. Respects API rate limits
4. Sufficient for 20 hospitals (max 10 seconds)

### Future Optimizations
- Parallel processing with asyncio.gather()
- Batch API calls if supported
- Progress tracking via WebSocket
- Resume capability for failed batches

---

## 🎓 Key Design Decisions

### 1. Why SQLite?
- ✅ Easy setup (no server)
- ✅ Perfect for development
- ✅ File-based (portable)
- ⚠️ For production: Use PostgreSQL

### 2. Why Sequential Processing?
- ✅ Simpler code
- ✅ Better error tracking
- ✅ Respects rate limits
- ⚠️ Slower (but acceptable for 20 hospitals)

### 3. Why Store History?
- ✅ Audit trail
- ✅ Debugging
- ✅ User can review past uploads
- ✅ Analytics

### 4. Why Batch Activation?
- ✅ Data consistency
- ✅ All-or-nothing approach
- ✅ Prevents partial data
- ✅ Matches business requirements

---

## 🚀 Summary

This system provides a **robust, well-architected solution** for bulk hospital uploads with:

✅ **Clean Architecture**: Separation of concerns  
✅ **Comprehensive Validation**: Multiple validation layers  
✅ **Error Handling**: Graceful failure handling  
✅ **Audit Trail**: Complete processing history  
✅ **User-Friendly**: Detailed feedback and documentation  
✅ **Production-Ready**: Deployment configuration included  
✅ **Well-Documented**: Comments throughout codebase  
✅ **Tested**: Unit tests for critical components  

The system is ready for deployment and can handle the specified requirements efficiently!
