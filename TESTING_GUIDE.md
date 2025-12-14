# Testing Guide - How to Test Your Hospital Bulk Processing API

## 📋 Table of Contents
1. [Setup and Run the Application](#setup-and-run-the-application)
2. [Test the API Endpoints](#test-the-api-endpoints)
3. [Check SQLite Database](#check-sqlite-database)
4. [Verify External API Integration](#verify-external-api-integration)
5. [Common Issues and Solutions](#common-issues-and-solutions)

---

## 🚀 Setup and Run the Application

### Step 1: Install Dependencies

```bash
# Make sure you're in the project directory
cd c:/Paribus

# Install required packages
pip install -r requirements.txt
```

### Step 2: Set Up Environment Variables

```bash
# Copy the example env file
copy .env.example .env

# Edit .env file and set:
# HOSPITAL_API_BASE_URL=https://hospital-directory.onrender.com
```

### Step 3: Run the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

### Step 4: Verify It's Running

Open your browser and go to:
- **API Docs**: http://127.0.0.1:8000/docs
- **Root Endpoint**: http://127.0.0.1:8000/
- **Health Check**: http://127.0.0.1:8000/health

---

## 🧪 Test the API Endpoints

### Method 1: Using Swagger UI (Easiest)

1. **Open Swagger UI**: http://127.0.0.1:8000/docs

2. **Test POST /hospitals/bulk**:
   - Click on "POST /hospitals/bulk"
   - Click "Try it out"
   - Click "Choose File" and select `sample_hospitals.csv`
   - Click "Execute"
   - See the response below

3. **Test GET /batches**:
   - Click on "GET /batches"
   - Click "Try it out"
   - Click "Execute"
   - See list of all batches

4. **Test GET /batches/{batch_id}**:
   - Copy a batch_id from previous response
   - Click on "GET /batches/{batch_id}"
   - Click "Try it out"
   - Paste the batch_id
   - Click "Execute"

### Method 2: Using cURL

```bash
# Test bulk upload
curl -X POST "http://127.0.0.1:8000/hospitals/bulk" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_hospitals.csv"

# Test list batches
curl -X GET "http://127.0.0.1:8000/batches"

# Test get batch details (replace with actual batch_id)
curl -X GET "http://127.0.0.1:8000/batches/550e8400-e29b-41d4-a716-446655440000"
```

### Method 3: Using Python Requests

```python
import requests

# Test bulk upload
with open('sample_hospitals.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://127.0.0.1:8000/hospitals/bulk', files=files)
    print(response.json())

# Test list batches
response = requests.get('http://127.0.0.1:8000/batches')
print(response.json())

# Test get batch details
batch_id = "your-batch-id-here"
response = requests.get(f'http://127.0.0.1:8000/batches/{batch_id}')
print(response.json())
```

---

## 🗄️ Check SQLite Database

### Method 1: Using DB Browser for SQLite (Recommended - GUI)

1. **Download DB Browser for SQLite**:
   - Go to: https://sqlitebrowser.org/dl/
   - Download and install for Windows

2. **Open Your Database**:
   - Launch DB Browser for SQLite
   - Click "Open Database"
   - Navigate to `c:/Paribus/hospital_bulk.db`
   - Click "Open"

3. **View Tables**:
   - Click "Browse Data" tab
   - Select "batch_uploads" from dropdown
   - See all batch records
   - Select "hospital_processing_results" from dropdown
   - See all hospital processing results

4. **Run SQL Queries**:
   - Click "Execute SQL" tab
   - Try these queries:

```sql
-- See all batches
SELECT * FROM batch_uploads ORDER BY created_at DESC;

-- See all hospital results
SELECT * FROM hospital_processing_results ORDER BY created_at DESC;

-- See results for a specific batch
SELECT * FROM hospital_processing_results 
WHERE batch_upload_id = 1;

-- Count hospitals by status
SELECT status, COUNT(*) as count 
FROM hospital_processing_results 
GROUP BY status;

-- See failed hospitals
SELECT * FROM hospital_processing_results 
WHERE status = 'failed';
```

### Method 2: Using SQLite Command Line

```bash
# Open SQLite database
sqlite3 hospital_bulk.db

# List all tables
.tables

# See batch_uploads table structure
.schema batch_uploads

# Query all batches
SELECT * FROM batch_uploads;

# Query hospital results
SELECT * FROM hospital_processing_results;

# Pretty print results
.mode column
.headers on
SELECT * FROM batch_uploads;

# Exit SQLite
.quit
```

### Method 3: Using Python Script

Create a file `check_db.py`:

```python
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('hospital_bulk.db')
cursor = conn.cursor()

print("=" * 80)
print("BATCH UPLOADS")
print("=" * 80)

# Query batches
cursor.execute("""
    SELECT batch_id, filename, total_hospitals, processed_hospitals, 
           failed_hospitals, batch_activated, status, created_at
    FROM batch_uploads
    ORDER BY created_at DESC
""")

batches = cursor.fetchall()
for batch in batches:
    print(f"\nBatch ID: {batch[0]}")
    print(f"Filename: {batch[1]}")
    print(f"Total: {batch[2]}, Processed: {batch[3]}, Failed: {batch[4]}")
    print(f"Activated: {batch[5]}, Status: {batch[6]}")
    print(f"Created: {batch[7]}")

print("\n" + "=" * 80)
print("HOSPITAL PROCESSING RESULTS")
print("=" * 80)

# Query hospital results
cursor.execute("""
    SELECT row_number, hospital_id, name, status, error_message
    FROM hospital_processing_results
    ORDER BY batch_upload_id, row_number
    LIMIT 10
""")

results = cursor.fetchall()
for result in results:
    print(f"\nRow {result[0]}: {result[2]}")
    print(f"Hospital ID: {result[1]}, Status: {result[3]}")
    if result[4]:
        print(f"Error: {result[4]}")

conn.close()
```

Run it:
```bash
python check_db.py
```

### Method 4: Using VS Code Extension

1. **Install SQLite Extension**:
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "SQLite"
   - Install "SQLite" by alexcvzz

2. **Open Database**:
   - Press Ctrl+Shift+P
   - Type "SQLite: Open Database"
   - Select `hospital_bulk.db`

3. **View Tables**:
   - Click on "SQLITE EXPLORER" in the sidebar
   - Expand your database
   - Right-click on a table → "Show Table"

---

## 🔍 Verify External API Integration

### Check if Hospitals Were Created in External API

```bash
# Get all hospitals from external API
curl -X GET "https://hospital-directory.onrender.com/hospitals/"

# Get hospitals for a specific batch
curl -X GET "https://hospital-directory.onrender.com/hospitals/batch/YOUR_BATCH_ID"
```

### Using Python:

```python
import requests

# Get all hospitals
response = requests.get('https://hospital-directory.onrender.com/hospitals/')
hospitals = response.json()
print(f"Total hospitals in external API: {len(hospitals)}")

# Get hospitals for specific batch
batch_id = "your-batch-id-here"
response = requests.get(f'https://hospital-directory.onrender.com/hospitals/batch/{batch_id}')
batch_hospitals = response.json()
print(f"Hospitals in batch {batch_id}: {len(batch_hospitals)}")
for hospital in batch_hospitals:
    print(f"- {hospital['name']} (ID: {hospital['id']}, Active: {hospital['active']})")
```

---

## 🧪 Complete Testing Workflow

### Test Case 1: Successful Bulk Upload

1. **Prepare CSV file** (`test_success.csv`):
```csv
name,address,phone
Test Hospital 1,123 Main St,555-0001
Test Hospital 2,456 Oak Ave,555-0002
Test Hospital 3,789 Pine Rd,555-0003
```

2. **Upload via API**:
```bash
curl -X POST "http://127.0.0.1:8000/hospitals/bulk" \
  -F "file=@test_success.csv"
```

3. **Expected Response**:
```json
{
  "batch_id": "...",
  "total_hospitals": 3,
  "processed_hospitals": 3,
  "failed_hospitals": 0,
  "batch_activated": true,
  "hospitals": [...]
}
```

4. **Check SQLite Database**:
```sql
-- Should see 1 new batch with status 'completed'
SELECT * FROM batch_uploads ORDER BY created_at DESC LIMIT 1;

-- Should see 3 new hospital results
SELECT * FROM hospital_processing_results 
WHERE batch_upload_id = (SELECT id FROM batch_uploads ORDER BY created_at DESC LIMIT 1);
```

5. **Check External API**:
```bash
# Replace with your batch_id
curl -X GET "https://hospital-directory.onrender.com/hospitals/batch/YOUR_BATCH_ID"
```

### Test Case 2: CSV with Validation Error

1. **Prepare CSV with too many rows** (`test_too_many.csv`):
```csv
name,address,phone
Hospital 1,Address 1,555-0001
Hospital 2,Address 2,555-0002
... (add 21+ rows)
```

2. **Upload via API**:
```bash
curl -X POST "http://127.0.0.1:8000/hospitals/bulk" \
  -F "file=@test_too_many.csv"
```

3. **Expected Response**:
```json
{
  "detail": "CSV file contains 21 rows, but maximum allowed is 20"
}
```

4. **Check Database**:
```sql
-- Should NOT see a new batch (validation failed before processing)
SELECT COUNT(*) FROM batch_uploads;
```

### Test Case 3: Invalid CSV Format

1. **Prepare invalid CSV** (`test_invalid.csv`):
```csv
hospital_name,location,contact
Test Hospital,123 Main St,555-0001
```

2. **Upload via API**:
```bash
curl -X POST "http://127.0.0.1:8000/hospitals/bulk" \
  -F "file=@test_invalid.csv"
```

3. **Expected Response**:
```json
{
  "detail": "Missing required header: name"
}
```

---

## 🐛 Common Issues and Solutions

### Issue 1: Database File Not Found

**Error**: `sqlite3.OperationalError: unable to open database file`

**Solution**:
```bash
# Make sure you're in the project directory
cd c:/Paribus

# The database will be created automatically when you run the app
uvicorn app.main:app --reload
```

### Issue 2: External API Connection Error

**Error**: `Request error: Connection refused`

**Solution**:
- Check your internet connection
- Verify the external API is running: https://hospital-directory.onrender.com/docs
- Check your `.env` file has correct `HOSPITAL_API_BASE_URL`

### Issue 3: Port Already in Use

**Error**: `OSError: [WinError 10048] Only one usage of each socket address`

**Solution**:
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001

# Or find and kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue 4: CSV File Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution**:
```bash
# Make sure the CSV file is in the current directory
dir sample_hospitals.csv

# Or use full path
curl -X POST "http://127.0.0.1:8000/hospitals/bulk" \
  -F "file=@C:/Paribus/sample_hospitals.csv"
```

---

## 📊 Quick Database Queries Reference

```sql
-- Count total batches
SELECT COUNT(*) as total_batches FROM batch_uploads;

-- Count completed vs failed batches
SELECT status, COUNT(*) as count 
FROM batch_uploads 
GROUP BY status;

-- Get latest batch
SELECT * FROM batch_uploads 
ORDER BY created_at DESC 
LIMIT 1;

-- Get all hospitals from latest batch
SELECT hr.* 
FROM hospital_processing_results hr
JOIN batch_uploads bu ON hr.batch_upload_id = bu.id
ORDER BY bu.created_at DESC, hr.row_number
LIMIT 20;

-- Count hospitals by status
SELECT status, COUNT(*) as count 
FROM hospital_processing_results 
GROUP BY status;

-- Get failed hospitals with errors
SELECT row_number, name, error_message 
FROM hospital_processing_results 
WHERE status = 'failed';

-- Get batch statistics
SELECT 
    bu.batch_id,
    bu.filename,
    bu.total_hospitals,
    bu.processed_hospitals,
    bu.failed_hospitals,
    bu.batch_activated,
    bu.processing_time_seconds,
    bu.status,
    COUNT(hr.id) as result_count
FROM batch_uploads bu
LEFT JOIN hospital_processing_results hr ON bu.id = hr.batch_upload_id
GROUP BY bu.id
ORDER BY bu.created_at DESC;
```

---

## ✅ Testing Checklist

- [ ] Application starts without errors
- [ ] Can access Swagger UI at /docs
- [ ] Can upload CSV file successfully
- [ ] Response includes batch_id and correct counts
- [ ] Can list all batches via GET /batches
- [ ] Can get batch details via GET /batches/{batch_id}
- [ ] SQLite database file is created
- [ ] batch_uploads table has records
- [ ] hospital_processing_results table has records
- [ ] Hospitals are created in external API
- [ ] Batch is activated in external API (if all succeeded)
- [ ] Validation errors are caught (too many rows, invalid format, etc.)
- [ ] Error messages are clear and helpful

---

## 🎯 Next Steps

After testing locally:

1. **Run Unit Tests**:
```bash
pytest tests/ -v
```

2. **Check Code Coverage**:
```bash
pytest --cov=app tests/
```

3. **Deploy to Render**:
   - Push code to GitHub
   - Connect Render to your repository
   - Render will use `render.yaml` for deployment

4. **Test Production**:
   - Use your production URL instead of localhost
   - Verify database persistence
   - Check logs for any errors

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLite Browser**: https://sqlitebrowser.org/
- **External API Docs**: https://hospital-directory.onrender.com/docs
- **Project Architecture**: See `ARCHITECTURE.md`
- **Flow Explanation**: See `FLOW_EXPLANATION.md`

Happy Testing! 🚀
