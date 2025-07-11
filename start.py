#!/usr/bin/env python3
"""
IoT DropSync - Start Script
Comprehensive startup script for the DropSync system
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

def initialize_directories():
    """Create necessary directories"""
    directories = [
        "app/uploads",
        "app/logs",
        "app/static"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def check_config_files():
    """Check if configuration files exist"""
    config_files = [
        "app/device_auth.json"
    ]
    
    for config_file in config_files:
        if not Path(config_file).exists():
            print(f"⚠️  Warning: {config_file} not found")
        else:
            print(f"✅ Found config file: {config_file}")

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting IoT DropSync Server...")
    print("Dashboard: http://localhost:8000/dashboard")
    print("API Docs: http://localhost:8000/api/v1/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        # Change to app directory
        os.chdir("app")
        
        # Start the server
        subprocess.run([
            sys.executable, "main.py"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except FileNotFoundError:
        print("❌ Error: Could not find main.py in app directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main function"""
    print("🔧 IoT DropSync - System Startup")
    print("=" * 50)
    
    # Run checks
    check_python_version()
    check_dependencies()
    initialize_directories()
    check_config_files()
    
    print("\n✅ All checks passed!")
    time.sleep(1)
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
