"""
Main entry point for running the FastAPI application.
This allows running the app using: python -m backend
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
