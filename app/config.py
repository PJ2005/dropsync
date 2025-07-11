import os
from pathlib import Path
from typing import Dict, Any

class Settings:
    """Application configuration settings"""
    
    # Base directories
    BASE_DIR = Path(__file__).resolve().parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    TEMPLATES_DIR = BASE_DIR.parent / "templates"
    STATIC_DIR = BASE_DIR / "static"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Database
    DATABASE_URL = f"sqlite:///{BASE_DIR}/dropsync.db"
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    DEVICE_AUTH_FILE = BASE_DIR / "device_auth.json"
    
    # API Settings
    API_V1_PREFIX = "/api/v1"
    PROJECT_NAME = "IoT DropSync"
    VERSION = "1.0.0"
    DESCRIPTION = "Secure Local File Transfer & Command Relay for Edge Devices"
    
    # File handling
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'.txt', '.log', '.json', '.csv', '.bin', '.hex', '.jpg', '.png'}
    
    # Device management
    DEVICE_TIMEOUT_MINUTES = 5
    MAX_COMMAND_QUEUE_SIZE = 100
    POLL_INTERVAL_SECONDS = 10
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_RETENTION_DAYS = 30
    MAX_LOG_ENTRIES = 10000
    
    # Network
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    
    # Features
    ENABLE_FILE_SYNC = True
    ENABLE_COMMAND_QUEUE = True
    ENABLE_DEVICE_DIAGNOSTICS = True
    ENABLE_WEB_DASHBOARD = True
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories"""
        for directory in [cls.UPLOAD_DIR, cls.STATIC_DIR, cls.LOGS_DIR]:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def get_device_upload_dir(cls, device_id: str) -> Path:
        """Get upload directory for a specific device"""
        device_dir = cls.UPLOAD_DIR / f"device-{device_id}"
        device_dir.mkdir(exist_ok=True)
        return device_dir
    
    @classmethod
    def get_sync_package_dir(cls, package_name: str) -> Path:
        """Get directory for sync packages"""
        package_dir = cls.UPLOAD_DIR / "packages" / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        return package_dir

# Global settings instance
settings = Settings()
