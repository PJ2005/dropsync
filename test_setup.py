#!/usr/bin/env python3
"""
Test script to verify the IoT DropSync module can be imported correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all modules can be imported"""
    print("Testing IoT DropSync imports...")
    
    try:
        # Test basic dependencies
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ Basic dependencies OK")
        
        # Test app module imports
        from app.config import settings
        print("✅ Config module OK")
        
        from app.database import init_database
        print("✅ Database module OK")
        
        from app.models import Device
        print("✅ Models module OK")
        
        from app.utils import DeviceManager
        print("✅ Utils module OK")
        
        from app.auth import auth_manager
        print("✅ Auth module OK")
        
        # Test API modules
        from app.api import device, files, admin
        print("✅ API modules OK")
        
        # Test main app
        from app.main import app
        print("✅ Main app module OK")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from app.config import settings
        
        print(f"✅ Project: {settings.PROJECT_NAME}")
        print(f"✅ Version: {settings.VERSION}")
        print(f"✅ Database: {settings.DATABASE_URL}")
        print(f"✅ Host: {settings.HOST}:{settings.PORT}")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    try:
        from app.database import init_database, SessionLocal
        
        # Initialize database
        init_database()
        print("✅ Database initialization OK")
        
        # Test session
        db = SessionLocal()
        db.close()
        print("✅ Database session OK")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 IoT DropSync - Module Test")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    print("\n" + "=" * 40)
    
    # Test config
    if not test_config():
        success = False
    
    print("\n" + "=" * 40)
    
    # Test database
    if not test_database():
        success = False
    
    print("\n" + "=" * 40)
    
    if success:
        print("🎉 All tests passed! The system is ready to run.")
        print("\nYou can now start the server with:")
        print("  python start.py")
        print("  or")
        print("  python run_server.py")
        print("  or")
        print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
