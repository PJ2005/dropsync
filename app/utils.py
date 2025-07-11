import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from .models import Device, Command, Message, FileSync, SyncPackage, SystemLog

class DeviceManager:
    """Manages device registration, authentication, and status tracking"""
    
    @staticmethod
    def register_device(db: Session, device_id: str, auth_token: str, 
                       device_type: str = "esp8266", name: str = None) -> Device:
        """Register a new device or update existing one"""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.auth_token = auth_token
            device.device_type = device_type
            device.name = name or device.name
            device.is_active = True
        else:
            device = Device(
                device_id=device_id,
                auth_token=auth_token,
                device_type=device_type,
                name=name or f"Device {device_id}"
            )
            db.add(device)
        
        db.commit()
        return device
    
    @staticmethod
    def update_device_status(db: Session, device_id: str, status: str = "online", 
                           ip_address: str = None, firmware_version: str = None):
        """Update device status and last seen timestamp"""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if device:
            device.status = status
            device.last_seen = datetime.utcnow()
            if ip_address:
                device.ip_address = ip_address
            if firmware_version:
                device.firmware_version = firmware_version
            db.commit()
    
    @staticmethod
    def get_active_devices(db: Session) -> List[Device]:
        """Get all active devices"""
        return db.query(Device).filter(Device.is_active == True).all()
    
    @staticmethod
    def is_device_online(device: Device, timeout_minutes: int = 5) -> bool:
        """Check if device is considered online based on last seen time"""
        if not device.last_seen:
            return False
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return device.last_seen > threshold

class CommandManager:
    """Manages command queue and execution"""
    
    @staticmethod
    def send_command(db: Session, device_id: str, command: str, 
                    parameters: Dict = None, priority: int = 1) -> Command:
        """Add a command to the queue for a specific device"""
        cmd = Command(
            device_id=device_id,
            command=command,
            parameters=json.dumps(parameters) if parameters else None,
            priority=priority
        )
        db.add(cmd)
        db.commit()
        
        # Log the command
        SystemLogger.log_event(db, "command_queued", "system", 
                              f"Command '{command}' queued for device {device_id}")
        return cmd
    
    @staticmethod
    def get_next_command(db: Session, device_id: str) -> Optional[Command]:
        """Get the next pending command for a device"""
        return db.query(Command).filter(
            Command.device_id == device_id,
            Command.status == "pending"
        ).order_by(Command.priority.desc(), Command.timestamp).first()
    
    @staticmethod
    def mark_command_sent(db: Session, command_id: int) -> bool:
        """Mark a command as sent"""
        cmd = db.query(Command).filter(Command.id == command_id).first()
        if cmd:
            cmd.status = "sent"
            cmd.sent_at = datetime.utcnow()
            db.commit()
            return True
        return False
    
    @staticmethod
    def complete_command(db: Session, command_id: int, result: str = None) -> bool:
        """Mark a command as completed with optional result"""
        cmd = db.query(Command).filter(Command.id == command_id).first()
        if cmd:
            cmd.status = "completed"
            cmd.completed_at = datetime.utcnow()
            cmd.result = result
            db.commit()
            return True
        return False

class FileManager:
    """Manages file operations and sync packages"""
    
    @staticmethod
    def calculate_file_hash(filepath: Path) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    @staticmethod
    def create_sync_package(db: Session, package_name: str, target_device_id: str,
                          package_type: str, description: str = None) -> SyncPackage:
        """Create a new sync package"""
        package = SyncPackage(
            package_name=package_name,
            target_device_id=target_device_id,
            package_type=package_type,
            description=description
        )
        db.add(package)
        db.commit()
        return package
    
    @staticmethod
    def track_file_sync(db: Session, device_id: str, filename: str, filepath: str,
                       sync_type: str = "upload") -> FileSync:
        """Track a file sync operation"""
        file_path = Path(filepath)
        file_size = file_path.stat().st_size if file_path.exists() else 0
        file_hash = FileManager.calculate_file_hash(file_path) if file_path.exists() else None
        
        sync = FileSync(
            device_id=device_id,
            filename=filename,
            filepath=filepath,
            file_size=file_size,
            file_hash=file_hash,
            sync_type=sync_type
        )
        db.add(sync)
        db.commit()
        return sync
    
    @staticmethod
    def get_device_files(upload_dir: Path, device_id: str) -> List[Dict]:
        """Get list of files for a specific device"""
        device_dir = upload_dir / f"device-{device_id}"
        files = []
        
        if device_dir.exists():
            for file_path in device_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "path": str(file_path)
                    })
        
        return files

class SystemLogger:
    """Centralized logging system"""
    
    @staticmethod
    def log_event(db: Session, event_type: str, source: str, message: str,
                 severity: str = "info", additional_data: Dict = None):
        """Log a system event"""
        log = SystemLog(
            event_type=event_type,
            source=source,
            message=message,
            severity=severity,
            additional_data=json.dumps(additional_data) if additional_data else None
        )
        db.add(log)
        db.commit()
    
    @staticmethod
    def log_device_message(db: Session, device_id: str, msg_type: str, content: str,
                          severity: str = "info") -> Message:
        """Log a message from a device"""
        message = Message(
            device_id=device_id,
            type=msg_type,
            content=content,
            severity=severity
        )
        db.add(message)
        db.commit()
        return message

class SecurityManager:
    """Security and authentication utilities"""
    
    @staticmethod
    def verify_device_token(db: Session, device_id: str, token: str) -> bool:
        """Verify device authentication token"""
        device = db.query(Device).filter(
            Device.device_id == device_id,
            Device.auth_token == token,
            Device.is_active == True
        ).first()
        return device is not None
    
    @staticmethod
    def generate_device_token(device_id: str) -> str:
        """Generate a secure token for a device"""
        # Simple token generation - in production, use proper cryptographic methods
        import secrets
        return secrets.token_urlsafe(32)

class ConfigManager:
    """Configuration management utilities"""
    
    @staticmethod
    def load_device_config(config_file: Path) -> Dict:
        """Load device configuration from JSON file"""
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_device_config(config_file: Path, config: Dict):
        """Save device configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def get_system_config() -> Dict:
        """Get system configuration"""
        return {
            "poll_interval": 10,  # seconds
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "device_timeout": 5,  # minutes
            "max_messages": 1000,
            "log_retention_days": 30
        }