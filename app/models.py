from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Device(Base):
    """Registered IoT devices in the system"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    device_type = Column(String, default="esp8266")
    auth_token = Column(String)
    last_seen = Column(DateTime, nullable=True)
    status = Column(String, default="offline")  # online, offline, error
    ip_address = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Command(Base):
    """Command queue for devices"""
    __tablename__ = "commands"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    command = Column(String)
    parameters = Column(Text, nullable=True)  # JSON string for command params
    status = Column(String, default="pending")  # pending, sent, completed, failed
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high
    timestamp = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)

class Message(Base):
    """Messages and logs from devices"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    type = Column(String)  # status, error, ack, log, diagnostic
    content = Column(Text)
    severity = Column(String, default="info")  # debug, info, warning, error, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)

class FileSync(Base):
    """File sync operations and history"""
    __tablename__ = "file_syncs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True)
    filename = Column(String)
    filepath = Column(String)
    file_size = Column(Integer)
    file_hash = Column(String, nullable=True)
    sync_type = Column(String)  # upload, download, delete
    status = Column(String, default="pending")  # pending, in_progress, completed, failed
    timestamp = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

class SyncPackage(Base):
    """Sync packages tagged for specific devices"""
    __tablename__ = "sync_packages"
    
    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String)
    target_device_id = Column(String, index=True)
    package_type = Column(String)  # firmware, config, data, script
    file_count = Column(Integer, default=0)
    total_size = Column(Integer, default=0)
    status = Column(String, default="staged")  # staged, deploying, deployed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)

class SystemLog(Base):
    """System-wide logs and events"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)  # device_connect, device_disconnect, command_sent, file_sync, error
    source = Column(String)  # system, device_id, or component name
    message = Column(Text)
    severity = Column(String, default="info")
    timestamp = Column(DateTime, default=datetime.utcnow)
    additional_data = Column(Text, nullable=True)  # JSON string for extra data