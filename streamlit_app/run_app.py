#!/usr/bin/env python3
"""
run_app.py - Cross-platform startup script for Football Analytics Platform

Usage:
    python run_app.py              # Run both services
    python run_app.py --backend    # Run only FastAPI backend
    python run_app.py --frontend   # Run only Streamlit frontend
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path

def print_header():
    print("\n" + "="*50)
    print("🚀 Football Analytics Platform Startup")
    print("="*50 + "\n")

def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} found")

def install_dependencies():
    """Install backend dependencies"""
    print("\n📦 Installing backend dependencies...")
    backend_req = Path("streamlit_app/backend/requirements.txt")
    
    if not backend_req.exists():
        print(f"⚠️  {backend_req} not found")
        return False
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(backend_req)],
            check=True
        )
        print("✓ Backend dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  Some dependencies may have failed to install")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path("streamlit_app/backend/.env")
    
    if env_file.exists():
        return
    
    print(f"\n⚠️  No .env file found in {env_file.parent}/")
    print("   Creating .env with sample configuration...")
    
    env_content = """\
# Backend environment configuration

# Snowflake (optional - defaults are in api.py)
SNOWFLAKE_ACCOUNT=your_snowflake_account_here
SNOWFLAKE_USER=MARK
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=sports_db
SNOWFLAKE_SCHEMA=analytics
SNOWFLAKE_WAREHOUSE=SPORTS_WH

# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Backend Configuration
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
"""
    
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text(env_content)
    print(f"   ✓ Created {env_file}")
    print("   ⚠️  UPDATE PASSWORD in .env before running!")

def start_backend():
    """Start FastAPI backend"""
    print("\n[Backend] Starting FastAPI on port 8000...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "streamlit_app.backend.api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start Streamlit frontend"""
    print("[Frontend] Starting Streamlit on port 8501...")
    cmd = [
        "streamlit", "run",
        "streamlit_app/app.py",
        "--server.port=8501",
        "--server.address=localhost"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    print("\n\nShutting down services...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="Football Analytics Platform Startup"
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Run only FastAPI backend"
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="Run only Streamlit frontend"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize
    print_header()
    check_python_version()
    install_dependencies()
    create_env_file()
    
    # Start services
    print("\n" + "="*50)
    print("🚀 Starting services...")
    print("="*50)
    print("\n1. FastAPI Backend")
    print("   URL: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("\n2. Streamlit Frontend")
    print("   URL: http://localhost:8501")
    print("\nPress Ctrl+C to stop services\n")
    
    processes = []
    
    if not args.frontend_only:
        backend = start_backend()
        if backend:
            processes.append(backend)
            time.sleep(2)  # Give backend time to start
    
    if not args.backend_only:
        frontend = start_frontend()
        if frontend:
            processes.append(frontend)
    
    if not processes:
        print("❌ No services could be started")
        sys.exit(1)
    
    try:
        # Wait for all processes
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down services...")
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
                process.wait()
        print("✓ Services stopped")

if __name__ == "__main__":
    main()
