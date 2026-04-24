"""FastAPI application entry point for InfraVersionHub."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import health
from src.config import get_settings
from src.logging_config import get_logger, setup_logging

# Initialize settings
settings = get_settings()

# Setup JSON logging
setup_logging(settings.log_level)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(
        "Starting InfraVersionHub",
        extra={
            "version": settings.app_version,
            "environment": settings.environment.value,
            "storage_backend": settings.storage_backend.value,
        },
    )

    # Initialize storage connector
    from src.storage import get_storage_connector

    storage = get_storage_connector()
    await storage.initialize()
    logger.info(f"Storage backend initialized: {settings.storage_backend.value}")

    yield

    # Shutdown
    logger.info("Shutting down InfraVersionHub")
    await storage.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Infrastructure Version Management Platform - Track and manage versions of infrastructure components across environments",
    version=settings.app_version,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Middleware to log all requests with request ID."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    response = await call_next(request)

    logger.info(
        f"Request completed: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "request_id": request_id,
        },
    )


# Include routers
app.include_router(health.router, prefix=settings.api_prefix)

# Import and include component, mapping, environment, and category routers
from src.api.routes import components, mappings, environments, categories

app.include_router(components.router, prefix=settings.api_prefix)
app.include_router(mappings.router, prefix=settings.api_prefix)
app.include_router(environments.router, prefix=settings.api_prefix)
app.include_router(categories.router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirecting to API documentation."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": f"{settings.api_prefix}/docs",
        "health": f"{settings.api_prefix}/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers,
        log_config=None,  # Disable uvicorn's default logging config
    )
