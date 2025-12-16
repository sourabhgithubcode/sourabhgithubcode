from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

from app.core.config import settings
from app.core.database import db
from app.api import listings, admin

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OPT/CPT Friendly Listings API",
    description="API for finding OPT and CPT friendly job and volunteer opportunities",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database and create necessary directories"""
    logger.info("Starting up application...")

    # Initialize database
    await db.initialize()

    # Create storage directories
    Path(settings.raw_html_path).mkdir(parents=True, exist_ok=True)
    Path(settings.raw_json_path).mkdir(parents=True, exist_ok=True)

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "OPT/CPT Friendly Listings API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "listings": "/listings",
            "listing_detail": "/listings/{id}",
            "scrape": "/admin/scrape",
            "assess": "/admin/assess",
            "override": "/admin/override/{id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        conn = await db.get_connection()
        cursor = await conn.execute("SELECT COUNT(*) FROM listings")
        count = (await cursor.fetchone())[0]
        await conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "listings_count": count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Include routers
app.include_router(listings.router)
app.include_router(admin.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
