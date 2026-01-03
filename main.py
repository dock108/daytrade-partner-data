"""
daytrade-partner-data — Backend API for TradeLens iOS app.

Entry point for the FastAPI application.
Run with: uvicorn app.main:app --reload
"""

import uvicorn

from app.main import app  # noqa: F401 - Re-export for uvicorn main:app

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
