"""
Application startup script.
Run the FastAPI application with Uvicorn.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.utils import get_settings


def main():
    """Start the application."""
    settings = get_settings()
    
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Host: {settings.api_host}:{settings.api_port}")
    print(f"Debug: {settings.debug}")
    print("-" * 50)
    
    # Note: reload mode disabled on Windows due to multiprocessing issues
    # For development with auto-reload, run: uvicorn src.main:app --reload
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,  # Disabled for Windows compatibility
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()
