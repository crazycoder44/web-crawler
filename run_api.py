#!/usr/bin/env python3
"""
Entry point for running the FastAPI server.
Provides RESTful API with authentication and rate limiting.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from src.api.main import app
from src.api.settings import settings


if __name__ == "__main__":
    print("🚀 Starting Books to Scrape API...")
    print(f"📍 Server: http://{settings.api_host}:{settings.api_port}")
    print(f"📚 Documentation: http://{settings.api_host}:{settings.api_port}/docs")
    print(f"🔒 Authentication: API Key required (X-API-Key header)")
    print(f"⏱️  Rate Limit: {settings.rate_limit_per_hour} requests/hour")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.api_log_level.lower()
    )
