"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import api_router
from src.services import get_cosmos_service
from src.utils import configure_logging, get_logger, get_settings


# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Data Analytics Chat Tool API...")
    settings = get_settings()
    
    try:
        # Initialize Cosmos DB service
        cosmos_service = get_cosmos_service()
        logger.info(f"Connected to Cosmos DB: {settings.cosmos_database_name}")
        logger.info("Cosmos DB containers initialized")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Data Analytics Chat Tool API...")
    try:
        # Cleanup resources
        cosmos_service = get_cosmos_service()
        # Close Cosmos client if needed
        logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered data analytics chat application with multi-agent architecture",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Data Analytics Chat Tool API",
            "version": settings.app_version,
            "docs": "/api/docs"
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Handle uncaught exceptions."""
        logger.error(f"Uncaught exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal server error occurred",
                "type": type(exc).__name__
            }
        )
    
    logger.info(f"FastAPI application created: {settings.app_name} v{settings.app_version}")
    
    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
