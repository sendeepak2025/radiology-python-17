#!/usr/bin/env python3
"""
Simple backend starter
"""

import uvicorn
from final_working_backend import app

if __name__ == "__main__":
    print("🚀 Starting Backend on port 8000...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        # Try port 8001 if 8000 fails
        print("🔄 Trying port 8001...")
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")