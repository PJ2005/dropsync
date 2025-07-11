#!/usr/bin/env python3
"""
IoT DropSync - Troubleshooting Script
Diagnose common issues with the setup
"""

import sys
import os
import subprocess
from pathlib import Path

def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")

def check_python():
    """Check Python version"""
    print_header("Python Version Check")
    print(f"Python version: {sys.version}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
        return True

def check_virtual_env():
    """Check if in virtual environment"""
    print_header("Virtual Environment Check")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        print(f"Virtual env path: {sys.prefix}")
        return True
    else:
        print("⚠️  Not in virtual environment")
        print("Consider using: python -m venv venv && source venv/bin/activate")
        return False

def check_dependencies():
    """Check if dependencies are installed"""
    print_header("Dependencies Check")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'jinja2',
        'python-multipart',
        'aiofiles'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\nTo install missing packages:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies installed")
        return True

def check_project_structure():
    """Check project structure"""
    print_header("Project Structure Check")
    
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/config.py',
        'app/database.py',
        'app/models.py',
        'app/utils.py',
        'app/auth.py',
        'requirements.txt'
    ]
    
    required_dirs = [
        'app/',
        'app/api/',
        'templates/',
        'esp8266_dropsync/'
    ]
    
    missing = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing.append(file_path)
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            missing.append(dir_path)
    
    return len(missing) == 0

def check_config_files():
    """Check configuration files"""
    print_header("Configuration Files Check")
    
    # Check device auth file
    auth_file = Path("app/device_auth.json")
    if auth_file.exists():
        print("✅ app/device_auth.json exists")
        try:
            import json
            with open(auth_file) as f:
                data = json.load(f)
            print(f"✅ Contains {len(data)} device configurations")
        except Exception as e:
            print(f"❌ Error reading device_auth.json: {e}")
    else:
        print("⚠️  app/device_auth.json missing - will create default")
    
    # Check directories
    dirs_to_check = ["app/uploads", "app/logs", "app/static"]
    for dir_path in dirs_to_check:
        if Path(dir_path).exists():
            print(f"✅ {dir_path} directory exists")
        else:
            print(f"⚠️  {dir_path} directory missing - will create")

def test_imports():
    """Test if modules can be imported"""
    print_header("Module Import Test")
    
    modules_to_test = [
        ('app.config', 'settings'),
        ('app.database', 'init_database'),
        ('app.models', 'Device'),
        ('app.utils', 'DeviceManager'),
        ('app.auth', 'auth_manager'),
        ('app.main', 'app')
    ]
    
    failed_imports = []
    
    for module_name, item_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print(f"✅ {module_name}.{item_name}")
        except ImportError as e:
            print(f"❌ {module_name}.{item_name} - Import Error: {e}")
            failed_imports.append(module_name)
        except AttributeError as e:
            print(f"❌ {module_name}.{item_name} - Attribute Error: {e}")
            failed_imports.append(module_name)
        except Exception as e:
            print(f"❌ {module_name}.{item_name} - Error: {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0

def suggest_fixes():
    """Suggest fixes for common issues"""
    print_header("Common Fixes")
    
    print("If you're having issues, try these steps:")
    print()
    print("1. Ensure you're in the project directory:")
    print("   cd /path/to/dropsync")
    print()
    print("2. Create and activate virtual environment:")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate  # Linux/Mac")
    print("   venv\\Scripts\\activate     # Windows")
    print()
    print("3. Install dependencies:")
    print("   pip install -r requirements.txt")
    print()
    print("4. Test the setup:")
    print("   python test_setup.py")
    print()
    print("5. Start the server:")
    print("   python start.py")
    print("   # OR")
    print("   python run_server.py")
    print("   # OR")
    print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print()
    print("6. If still having issues, check:")
    print("   - Python version (3.8+ required)")
    print("   - File permissions")
    print("   - Network connectivity")
    print("   - Firewall settings")

def main():
    """Main troubleshooting function"""
    print("🔍 IoT DropSync - Troubleshooting Tool")
    print("This tool will help diagnose common setup issues")
    
    checks = [
        check_python(),
        check_virtual_env(),
        check_dependencies(),
        check_project_structure(),
        test_imports()
    ]
    
    check_config_files()
    
    print_header("Summary")
    
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print("🎉 All checks passed! Your setup looks good.")
        print("\nYou can start the server with:")
        print("  python start.py")
    else:
        print(f"❌ {total - passed} out of {total} checks failed.")
        suggest_fixes()

if __name__ == "__main__":
    main()
