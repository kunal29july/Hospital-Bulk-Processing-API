# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================
# This file initializes the FastAPI application and configures:
# 1. Database initialization on startup
# 2. CORS middleware for cross-origin requests
# 3. API routes from app.api.endpoints
# 
# FLOW:
# 1. Application starts → lifespan() initializes database
# 2. Incoming requests → CORS middleware → router endpoints
# 3. Router endpoints (app/api/endpoints.py) handle business logic
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.api import hospitals, batches


# ============================================================================
# LIFESPAN MANAGEMENT
# ============================================================================
# Handles application startup and shutdown events
# FLOW: App starts → init_db() creates tables → App runs → Cleanup on shutdown
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup: Initialize database tables (creates Batch and HospitalRecord tables)
    init_db()
    yield
    # Shutdown: cleanup if needed (database connections auto-close)


# ============================================================================
# FASTAPI APPLICATION INSTANCE
# ============================================================================
# Creates the main FastAPI app with lifespan management
# ============================================================================
app = FastAPI(
    title="Hospital Bulk Processing API",
    description="API for bulk processing hospital records via CSV upload",
    version="1.0.0",
    lifespan=lifespan  # Connects lifespan handler for startup/shutdown
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================
# CORS middleware allows cross-origin requests from any domain
# FLOW: Request → CORS validation → Next middleware/endpoint
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================
# Includes API endpoints from separate router modules
# FLOW: Request → Middleware → Router → Endpoint handler
# 
# You can Ctrl+Click (or Cmd+Click) on the router names below to navigate
# to their implementation files:
# 
# hospitals.router → app/api/hospitals.py
#   - POST /hospitals/bulk → Bulk upload CSV
# 
# batches.router → app/api/batches.py
#   - GET /batches → List all batches
#   - GET /batches/{batch_id} → Get batch details
# ============================================================================
app.include_router(hospitals.router, tags=["Hospitals"])
app.include_router(batches.router, tags=["Batches"])


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================
# These are defined directly on the app (not in router)
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API information and available endpoints
    FLOW: GET / → Returns API metadata
    """
    return {
        "message": "Hospital Bulk Processing API",
        "version": "1.0.0",
        "endpoints": {
            "bulk_upload": "POST /hospitals/bulk",
            "list_batches": "GET /batches",
            "get_batch": "GET /batches/{batch_id}",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - Used for monitoring/load balancers
    FLOW: GET /health → Returns healthy status
    """
    return {"status": "healthy"}
