"""Main entry point for the FastAPI application."""

import uvicorn
from app import create_app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
