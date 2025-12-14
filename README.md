# Hospital Bulk Processing API

A FastAPI-based bulk processing system that integrates with the Hospital Directory API to handle CSV uploads and process hospital records in batches.

## Features

- ✅ Bulk upload hospitals via CSV file (max 20 hospitals)
- ✅ Automatic batch ID generation and tracking
- ✅ Sequential processing with detailed error handling
- ✅ **Intelligent retry mechanism with exponential backoff**
- ✅ **API warmup to handle cold starts**
- ✅ **90-second timeout for slow external APIs**
- ✅ Batch activation after successful processing
- ✅ SQLite database for processing history
- ✅ Comprehensive validation and error reporting
- ✅ RESTful API with automatic documentation
- ✅ Bonus: List all batches and get batch details

## Tech Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **SQLite** - Lightweight database
- **Pydantic** - Data validation
- **httpx** - Async HTTP client
- **pytest** - Testing framework

## Project Structure

```
hospital-bulk-processor/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── database.py             # Database setup
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints.py        # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── csv_processor.py   # CSV parsing & validation
│   │   └── hospital_client.py # HTTP client for Hospital API
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_csv_processor.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── sample_hospitals.csv        # Sample CSV for testing
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd hospital-bulk-processor
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- Linux/Mac:
  ```bash
  source venv/bin/activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create `.env` file (optional):
```bash
cp .env.example .env
```

Edit `.env` if you need to change default settings:
```
HOSPITAL_API_BASE_URL=https://hospital-directory.onrender.com
DATABASE_URL=sqlite:///./hospital_bulk.db
MAX_CSV_ROWS=20
```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Bulk Upload Hospitals

**Endpoint**: `POST /hospitals/bulk`

**Description**: Upload a CSV file to create multiple hospitals in batch

**Request**:
- Content-Type: `multipart/form-data`
- Body: CSV file with headers: `name,address,phone` (phone is optional)

**CSV Format**:
```csv
name,address,phone
City General Hospital,123 Main Street,555-0101
St. Mary's Medical Center,456 Oak Avenue,555-0102
Memorial Hospital,789 Pine Road,555-0103
```

**Response**:
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_hospitals": 3,
  "processed_hospitals": 3,
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
    }
  ]
}
```

### 2. List All Batches

**Endpoint**: `GET /batches`

**Description**: Get a list of all batch uploads

**Response**:
```json
[
  {
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "hospitals.csv",
    "total_hospitals": 3,
    "processed_hospitals": 3,
    "failed_hospitals": 0,
    "batch_activated": true,
    "status": "completed",
    "created_at": "2025-12-14T10:30:00Z",
    "completed_at": "2025-12-14T10:30:05Z"
  }
]
```

### 3. Get Batch Details

**Endpoint**: `GET /batches/{batch_id}`

**Description**: Get detailed results for a specific batch

**Response**: Same format as bulk upload response

### 4. Health Check

**Endpoint**: `GET /health`

**Description**: Check if the API is running

**Response**:
```json
{
  "status": "healthy"
}
```

## Testing with cURL

### Upload CSV file:
```bash
curl -X POST "http://localhost:8000/hospitals/bulk" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_hospitals.csv"
```

### List all batches:
```bash
curl -X GET "http://localhost:8000/batches"
```

### Get batch details:
```bash
curl -X GET "http://localhost:8000/batches/{batch_id}"
```

## Testing with Python

```python
import requests

# Upload CSV
with open('sample_hospitals.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/hospitals/bulk',
        files={'file': f}
    )
    print(response.json())

# List batches
response = requests.get('http://localhost:8000/batches')
print(response.json())
```

## Running Tests

```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

## Architecture & Design

### System Architecture

The application follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│                    app/api/hospitals.py                      │
│              - Request handling & validation                 │
│              - Response formatting                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Service Layer                              │
│  ┌─────────────────────────┐  ┌────────────────────────┐   │
│  │   CSV Processor         │  │  Hospital API Client   │   │
│  │ csv_processor.py        │  │ hospital_client.py     │   │
│  │ - CSV validation        │  │ - HTTP communication   │   │
│  │ - Data parsing          │  │ - Retry logic          │   │
│  │ - Business rules        │  │ - API warmup           │   │
│  └─────────────────────────┘  └────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Data Layer (SQLAlchemy)                     │
│                   app/models.py                              │
│              - Database models                               │
│              - ORM operations                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   SQLite Database                            │
│              - BatchUpload table                             │
│              - HospitalProcessingResult table                │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Patterns

1. **Service Layer Pattern**: Business logic separated from API endpoints
2. **Repository Pattern**: Database operations abstracted through SQLAlchemy ORM
3. **Dependency Injection**: FastAPI's `Depends()` for database sessions
4. **DTO Pattern**: Pydantic schemas for data validation and serialization

## Processing Workflow

### Standard Flow (8 Steps)

1. **CSV Upload & Validation**
   - User uploads CSV file via POST request
   - System validates CSV format, headers, and row count (max 20)
   - Parses CSV into structured data

2. **Batch ID Generation**
   - Generate unique UUID for batch tracking
   - Ensures idempotency and traceability

3. **Database Record Creation**
   - Create `BatchUpload` record with status "PROCESSING"
   - Commit to database for tracking

4. **🆕 API Warmup (Cold Start Prevention)**
   - Send GET request to external API
   - Wakes up service if in cold start (Render free tier)
   - Prevents first hospital from timing out

5. **Sequential Hospital Processing**
   - For each hospital in CSV:
     - Validate hospital data (name, address required)
     - **🆕 Retry Logic**: Attempt creation up to 3 times
       - Attempt 1: Initial request (90s timeout)
       - Attempt 2: Wait 5s, retry (90s timeout)
       - Attempt 3: Wait 5s, final retry (90s timeout)
     - Store result in `HospitalProcessingResult` table
     - Continue to next hospital regardless of failure

6. **Batch Activation**
   - If ALL hospitals succeeded: Call external API to activate batch
   - If ANY hospital failed: Skip activation, mark batch as FAILED

7. **Database Update**
   - Update `BatchUpload` with final counts and status
   - Record processing time and completion timestamp

8. **Response Generation**
   - Return comprehensive results with per-hospital details
   - Include batch ID for future reference

### Retry Mechanism Details

**Problem Solved**: External API cold starts and transient network failures

**Approach Used**: Intelligent retry with exponential backoff

```
Hospital Creation Attempt Flow:
┌─────────────────────────────────────────────────────────────┐
│ Attempt 1: POST /hospitals/ (90s timeout)                   │
│   ├─ Success? → Return hospital data                        │
│   └─ Failure? → Check error type                            │
│       ├─ 4xx Client Error? → Don't retry (permanent error)  │
│       └─ 5xx/Timeout/Network? → Wait 5s, proceed to Attempt 2│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ Attempt 2: Retry POST /hospitals/ (90s timeout)             │
│   ├─ Success? → Return hospital data                        │
│   └─ Failure? → Wait 5s, proceed to Attempt 3               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│ Attempt 3: Final Retry POST /hospitals/ (90s timeout)       │
│   ├─ Success? → Return hospital data                        │
│   └─ Failure? → Mark as FAILED, log error                   │
└─────────────────────────────────────────────────────────────┘
```

**Configuration**:
- **Timeout**: 90 seconds (handles cold starts)
- **Max Retries**: 2 (total 3 attempts)
- **Retry Delay**: 5 seconds between attempts
- **Smart Retry**: Skips retry for 4xx client errors

**Benefits**:
- ✅ Handles cold starts gracefully (first request may take 30-60s)
- ✅ Recovers from transient network failures
- ✅ Doesn't waste time retrying permanent errors (4xx)
- ✅ Detailed logging for debugging
- ✅ Production-ready reliability

## Problems Solved & Solutions

### Problem 1: External API Cold Starts
**Issue**: First API call after inactivity takes 30-90 seconds (Render free tier)  
**Impact**: First hospital in batch would timeout  
**Solution**: 
- Added `warmup_api()` method that pings API before processing
- Wakes up service proactively
- Subsequent requests complete in 5-10 seconds

### Problem 2: Transient Network Failures
**Issue**: Occasional timeouts or network errors during processing  
**Impact**: Valid hospitals marked as failed due to temporary issues  
**Solution**:
- Implemented retry logic with 3 attempts per hospital
- 5-second delays between retries
- Smart retry: skips 4xx errors (won't succeed anyway)

### Problem 3: Database Locking (SQLite)
**Issue**: Multiple processes accessing SQLite caused "database is locked" errors  
**Impact**: Batch processing would fail mid-operation  
**Solution**:
- Added retry logic for database commits
- Proper transaction management
- Clear error messages for users

### Problem 4: Batch Processing with 20 Hospitals
**Issue**: Processing 20 hospitals sequentially could take 3-5 minutes  
**Impact**: Long wait times, increased chance of failures  
**Solution**:
- API warmup reduces cold start impact
- Retry logic ensures transient failures don't fail entire batch
- Detailed progress logging for monitoring
- Continue processing even if some hospitals fail

## Error Handling

The system handles various error scenarios:

- **Invalid CSV format**: Returns 400 with specific error message
- **Missing required fields**: Returns 400 with row number and field name
- **Too many rows**: Returns 400 if exceeds 20 hospitals
- **API failures**: Records error per hospital, continues processing
- **Partial failures**: If any hospital fails, batch is not activated

## Database Schema

### BatchUpload Table
- Tracks each CSV upload
- Stores batch metadata and processing results
- Links to individual hospital results

### HospitalProcessingResult Table
- Stores result for each hospital in a batch
- Includes hospital ID from API (if successful)
- Records error messages for failures

## Deployment

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables:
   - `HOSPITAL_API_BASE_URL`: https://hospital-directory.onrender.com
   - `DATABASE_URL`: sqlite:///./hospital_bulk.db
   - `MAX_CSV_ROWS`: 20

### Alternative: render.yaml

Create `render.yaml` in project root:
```yaml
services:
  - type: web
    name: hospital-bulk-processor
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: HOSPITAL_API_BASE_URL
        value: https://hospital-directory.onrender.com
      - key: DATABASE_URL
        value: sqlite:///./hospital_bulk.db
      - key: MAX_CSV_ROWS
        value: 20
```

## Configuration

All configuration is managed through environment variables (see `.env.example`):

- `HOSPITAL_API_BASE_URL`: Base URL of the Hospital Directory API
- `DATABASE_URL`: SQLite database connection string
- `MAX_CSV_ROWS`: Maximum number of hospitals per CSV (default: 20)

## Limitations

- Maximum 20 hospitals per CSV upload
- Sequential processing (not parallel)
- SQLite database (suitable for development/small scale)
- No authentication/authorization implemented

## Production Considerations

### Scalability
- **Current**: Sequential processing, suitable for up to 20 hospitals per batch
- **Recommendation**: For higher volumes, consider parallel processing with rate limiting

### Database
- **Current**: SQLite (suitable for development and small-scale deployments)
- **Production**: Consider PostgreSQL or MySQL for:
  - Better concurrency handling
  - ACID compliance at scale
  - Connection pooling
  - Replication and backup capabilities

### Monitoring & Observability
- Implement structured logging (JSON format)
- Add application metrics (Prometheus/Grafana)
- Set up error tracking (Sentry, Rollbar)
- Monitor API response times and success rates

### Security
- Add API authentication (JWT, OAuth2)
- Implement rate limiting per user/IP
- Add CORS configuration for production domains
- Validate and sanitize all user inputs
- Use HTTPS in production

### High Availability
- Deploy multiple instances behind a load balancer
- Implement health checks for auto-recovery
- Use managed database services
- Set up automated backups

## Future Enhancements

- [ ] Parallel processing with configurable concurrency
- [ ] WebSocket support for real-time progress updates
- [ ] Resume capability for failed batches
- [ ] CSV validation endpoint (dry-run mode)
- [ ] PostgreSQL/MySQL support
- [ ] Authentication and authorization (JWT)
- [ ] Rate limiting per user
- [ ] Batch deletion and rollback endpoints
- [ ] Export batch results to CSV/Excel
- [ ] Email notifications for batch completion

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.
