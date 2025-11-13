"""
Settings Service
Refactored with modular routes for better maintainability
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from database import init_db

# Import routes
from routes.health import router as health_router
from routes.api_keys import router as api_keys_router
from routes.settings import router as settings_router
from routes.usage import router as usage_router

# Create FastAPI app
app = FastAPI(title="Settings Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    os.makedirs('data', exist_ok=True)
    init_db()


# Include routers
app.include_router(health_router)
app.include_router(api_keys_router)
app.include_router(settings_router)
app.include_router(usage_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
