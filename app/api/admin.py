from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_db
from ..models import Device, Command, Message, SyncPackage
from ..utils import DeviceManager, CommandManager, FileManager, SystemLogger
from ..auth import auth_manager

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/devices")
async def list_devices(
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False)
):
    """List all registered devices"""
    if include_inactive:
        devices = db.query(Device).all()
    else:
        devices = DeviceManager.get_active_devices(db)
    
    device_list = []
    for device in devices:
        device_data = {
            "id": device.id,
            "device_id": device.device_id,
            "name": device.name,
            "device_type": device.device_type,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "ip_address": device.ip_address,
            "firmware_version": device.firmware_version,
            "created_at": device.created_at.isoformat(),
            "is_active": device.is_active,
            "is_online": DeviceManager.is_device_online(device)
        }
        device_list.append(device_data)
    
    return {"devices": device_list}

@router.post("/devices/register")
async def register_device(
    device_id: str = Form(...),
    name: str = Form(None),
    device_type: str = Form("esp8266"),
    db: Session = Depends(get_db)
):
    """Register a new device"""
    # Generate token
    token = auth_manager.generate_device_token(device_id)
    
    # Register device
    device = DeviceManager.register_device(db, device_id, token, device_type, name)
    
    SystemLogger.log_event(
        db, "device_registered", "admin",
        f"Device {device_id} registered by admin"
    )
    
    return {
        "device_id": device_id,
        "token": token,
        "name": device.name,
        "device_type": device.device_type,
        "status": "registered"
    }

@router.post("/devices/{device_id}/command")
async def send_command_to_device(
    device_id: str,
    command: str = Form(...),
    parameters: str = Form(None),
    priority: int = Form(1),
    db: Session = Depends(get_db)
):
    """Send a command to a specific device"""
    # Check if device exists
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Parse parameters if provided
    params = None
    if parameters:
        try:
            params = json.loads(parameters)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON parameters")
    
    # Send command
    cmd = CommandManager.send_command(db, device_id, command, params, priority)
    
    return {
        "command_id": cmd.id,
        "device_id": device_id,
        "command": command,
        "parameters": params,
        "priority": priority,
        "status": "queued"
    }

@router.get("/devices/{device_id}/commands")
async def get_device_commands(
    device_id: str,
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get command history for a device"""
    commands = db.query(Command).filter(
        Command.device_id == device_id
    ).order_by(Command.timestamp.desc()).limit(limit).all()
    
    return {
        "device_id": device_id,
        "commands": [
            {
                "id": cmd.id,
                "command": cmd.command,
                "parameters": cmd.parameters,
                "status": cmd.status,
                "priority": cmd.priority,
                "timestamp": cmd.timestamp.isoformat(),
                "sent_at": cmd.sent_at.isoformat() if cmd.sent_at else None,
                "completed_at": cmd.completed_at.isoformat() if cmd.completed_at else None,
                "result": cmd.result
            }
            for cmd in commands
        ]
    }

@router.get("/devices/{device_id}/messages")
async def get_device_messages(
    device_id: str,
    limit: int = Query(50, le=100),
    severity: str = Query(None),
    db: Session = Depends(get_db)
):
    """Get messages from a device"""
    query = db.query(Message).filter(Message.device_id == device_id)
    
    if severity:
        query = query.filter(Message.severity == severity)
    
    messages = query.order_by(Message.timestamp.desc()).limit(limit).all()
    
    return {
        "device_id": device_id,
        "messages": [
            {
                "id": msg.id,
                "type": msg.type,
                "content": msg.content,
                "severity": msg.severity,
                "timestamp": msg.timestamp.isoformat(),
                "acknowledged": msg.acknowledged
            }
            for msg in messages
        ]
    }

@router.post("/sync-packages")
async def create_sync_package(
    package_name: str = Form(...),
    target_device_id: str = Form(...),
    package_type: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    """Create a new sync package"""
    # Check if device exists
    device = db.query(Device).filter(Device.device_id == target_device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Target device not found")
    
    # Create package
    package = FileManager.create_sync_package(
        db, package_name, target_device_id, package_type, description
    )
    
    SystemLogger.log_event(
        db, "package_created", "admin",
        f"Sync package '{package_name}' created for device {target_device_id}"
    )
    
    return {
        "package_id": package.id,
        "package_name": package_name,
        "target_device_id": target_device_id,
        "package_type": package_type,
        "status": "staged"
    }

@router.get("/sync-packages")
async def list_sync_packages(
    device_id: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """List sync packages"""
    query = db.query(SyncPackage)
    
    if device_id:
        query = query.filter(SyncPackage.target_device_id == device_id)
    
    if status:
        query = query.filter(SyncPackage.status == status)
    
    packages = query.order_by(SyncPackage.created_at.desc()).all()
    
    return {
        "packages": [
            {
                "id": pkg.id,
                "package_name": pkg.package_name,
                "target_device_id": pkg.target_device_id,
                "package_type": pkg.package_type,
                "file_count": pkg.file_count,
                "total_size": pkg.total_size,
                "status": pkg.status,
                "created_at": pkg.created_at.isoformat(),
                "deployed_at": pkg.deployed_at.isoformat() if pkg.deployed_at else None,
                "description": pkg.description
            }
            for pkg in packages
        ]
    }

@router.post("/devices/{device_id}/revoke-token")
async def revoke_device_token(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Revoke a device token"""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    auth_manager.revoke_device_token(device_id, db)
    
    return {"status": "revoked", "device_id": device_id}

@router.get("/system/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.is_active == True).count()
    online_devices = len([
        d for d in db.query(Device).filter(Device.is_active == True).all()
        if DeviceManager.is_device_online(d)
    ])
    
    pending_commands = db.query(Command).filter(Command.status == "pending").count()
    total_messages = db.query(Message).count()
    
    return {
        "devices": {
            "total": total_devices,
            "active": active_devices,
            "online": online_devices
        },
        "commands": {
            "pending": pending_commands
        },
        "messages": {
            "total": total_messages
        }
    }
