"""
Enhanced API Gateway with Integration Features
- Retry logic with httpx-retries
- Circuit breakers for fault tolerance
- Comprehensive error handling
- Request/response logging
- Health check aggregation

Refactored with modular routers for better maintainability
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from dependencies import service_registry
from middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware

# Import routers
from routers import health, documents, trees, queries, chat, settings, conversations, cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Register all services
    logger.info("Starting API Gateway")

    service_registry.register("documents", "http://document-service:8001", max_retries=3, timeout=60.0)
    service_registry.register("trees", "http://tree-service:8002", max_retries=3, timeout=300.0)
    service_registry.register("queries", "http://query-service:8003", max_retries=3, timeout=120.0)
    service_registry.register("chat", "http://chat-service:8004", max_retries=2, timeout=180.0)
    service_registry.register("storage", "http://storage-service:8005", max_retries=3, timeout=30.0)
    service_registry.register("cache", "http://cache-service:8006", max_retries=2, timeout=10.0)
    service_registry.register("settings", "http://settings-service:8007", max_retries=3, timeout=30.0)

    logger.info(f"Registered {len(service_registry.services)} services")

    yield

    # Shutdown: Close all connections
    logger.info("Shutting down API Gateway")
    await service_registry.close_all()


# Initialize FastAPI with lifespan
app = FastAPI(
    title="API Gateway",
    version="2.0.0",
    description="Central gateway with retry logic, circuit breakers, and fault tolerance",
    lifespan=lifespan
)

# Add middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Retry logic with httpx-retries",
            "Circuit breakers for fault tolerance",
            "Comprehensive error handling",
            "Request/response logging",
            "Health check aggregation"
        ],
        "services": list(service_registry.services.keys())
    }


# Include all routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(trees.router)
app.include_router(queries.router)
app.include_router(chat.router)
app.include_router(settings.router)
app.include_router(settings.usage_router)  # Usage endpoints from settings module
app.include_router(conversations.router)
app.include_router(cache.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
