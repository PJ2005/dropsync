import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import get_db
from .models import Device
from .config import settings
from .utils import SystemLogger

security = HTTPBearer()

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class DeviceAuthManager:
    """Manages device authentication and authorization"""
    
    def __init__(self):
        self.device_tokens = self._load_device_tokens()
    
    def _load_device_tokens(self) -> Dict[str, str]:
        """Load device tokens from file"""
        try:
            if settings.DEVICE_AUTH_FILE.exists():
                with open(settings.DEVICE_AUTH_FILE, 'r') as f:
                    return json.load(f)
            else:
                # Create default token file
                default_tokens = {"esp001": "abc123"}
                self._save_device_tokens(default_tokens)
                return default_tokens
        except Exception as e:
            print(f"Error loading device tokens: {e}")
            return {}
    
    def _save_device_tokens(self, tokens: Dict[str, str]):
        """Save device tokens to file"""
        try:
            with open(settings.DEVICE_AUTH_FILE, 'w') as f:
                json.dump(tokens, f, indent=2)
        except Exception as e:
            print(f"Error saving device tokens: {e}")
    
    def verify_device_token(self, device_id: str, token: str, db: Session) -> bool:
        """Verify device token against database and file"""
        # Check database first
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.auth_token == token,
            Device.is_active == True
        ).first()
        
        if device:
            # Update last seen
            device.last_seen = datetime.utcnow()
            device.status = "online"
            db.commit()
            return True
        
        # Fallback to file-based tokens for backward compatibility
        if device_id in self.device_tokens and self.device_tokens[device_id] == token:
            # Register device in database if not exists
            self._register_device_from_token(device_id, token, db)
            return True
        
        return False
    
    def _register_device_from_token(self, device_id: str, token: str, db: Session):
        """Register device in database from token file"""
        device = Device(
            device_id=device_id,
            auth_token=token,
            name=f"Device {device_id}",
            device_type="esp8266",
            status="online",
            last_seen=datetime.utcnow()
        )
        db.add(device)
        db.commit()
        
        SystemLogger.log_event(
            db, "device_registered", "system",
            f"Device {device_id} registered from token file"
        )
    
    def generate_device_token(self, device_id: str) -> str:
        """Generate a new secure token for a device"""
        token = secrets.token_urlsafe(32)
        self.device_tokens[device_id] = token
        self._save_device_tokens(self.device_tokens)
        return token
    
    def revoke_device_token(self, device_id: str, db: Session):
        """Revoke a device token"""
        # Remove from file
        if device_id in self.device_tokens:
            del self.device_tokens[device_id]
            self._save_device_tokens(self.device_tokens)
        
        # Deactivate in database
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.is_active = False
            device.status = "disabled"
            db.commit()
        
        SystemLogger.log_event(
            db, "device_revoked", "system",
            f"Device {device_id} token revoked"
        )

# Global auth manager instance
auth_manager = DeviceAuthManager()

def verify_device_auth(device_id: str, token: str, db: Session = Depends(get_db)):
    """Dependency to verify device authentication"""
    if not auth_manager.verify_device_token(device_id, token, db):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized device or invalid token"
        )
    return device_id

def get_current_device(request: Request, db: Session = Depends(get_db)) -> Optional[Device]:
    """Get current device from request"""
    # Extract device_id from URL or headers
    device_id = request.path_params.get("device_id")
    if not device_id:
        return None
    
    return db.query(Device).filter(Device.device_id == device_id).first()

def require_device_auth(device_id: str, token: str, db: Session = Depends(get_db)):
    """Require valid device authentication"""
    device = db.query(Device).filter(
        Device.device_id == device_id,
        Device.auth_token == token,
        Device.is_active == True
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=403,
            detail="Unauthorized device or invalid token"
        )
    
    # Update device status
    device.last_seen = datetime.utcnow()
    device.status = "online"
    db.commit()
    
    return device

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        # Check if within limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False

# Global rate limiter
rate_limiter = RateLimiter()
