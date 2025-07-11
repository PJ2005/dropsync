from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import Device, Command, Message
from ..utils import DeviceManager, CommandManager, SystemLogger
from ..auth import require_device_auth, rate_limiter

router = APIRouter(prefix="/device", tags=["device"])

@router.get("/ping/{device_id}")
async def ping_device(
    device_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Device ping endpoint to check connectivity"""
    # Rate limiting
    if not rate_limiter.is_allowed(f"ping_{device_id}"):
        raise HTTPException(status_code=429, detail="Too many requests")
    
    device = require_device_auth(device_id, token, db)
    
    # Update device status
    DeviceManager.update_device_status(db, device_id, "online")
    
    return {
        "status": "ok",
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Device ping successful"
    }

@router.get("/commands/{device_id}")
async def get_device_commands(
    device_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get pending commands for a device"""
    device = require_device_auth(device_id, token, db)
    
    # Get next command
    command = CommandManager.get_next_command(db, device_id)
    
    if command:
        # Mark as sent
        CommandManager.mark_command_sent(db, command.id)
        
        SystemLogger.log_event(
            db, "command_sent", device_id,
            f"Command '{command.command}' sent to device {device_id}"
        )
        
        return {
            "command_id": command.id,
            "command": command.command,
            "parameters": command.parameters,
            "priority": command.priority,
            "timestamp": command.timestamp.isoformat()
        }
    
    return {"command": "none", "message": "No pending commands"}

@router.post("/commands/{device_id}/complete")
async def complete_command(
    device_id: str,
    command_id: int = Form(...),
    result: str = Form(None),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Mark a command as completed"""
    device = require_device_auth(device_id, token, db)
    
    success = CommandManager.complete_command(db, command_id, result)
    
    if success:
        SystemLogger.log_event(
            db, "command_completed", device_id,
            f"Command {command_id} completed by device {device_id}"
        )
        return {"status": "completed", "command_id": command_id}
    
    raise HTTPException(status_code=404, detail="Command not found")

@router.post("/messages/{device_id}")
async def send_device_message(
    device_id: str,
    msg_type: str = Form(...),
    content: str = Form(...),
    severity: str = Form("info"),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Receive a message from a device"""
    device = require_device_auth(device_id, token, db)
    
    # Update device status
    DeviceManager.update_device_status(db, device_id, "online")
    
    # Log the message
    message = SystemLogger.log_device_message(db, device_id, msg_type, content, severity)
    
    # Log system event for important messages
    if severity in ["warning", "error", "critical"]:
        SystemLogger.log_event(
            db, "device_alert", device_id,
            f"Device {device_id} reported {severity}: {content}",
            severity
        )
    
    return {
        "status": "logged",
        "message_id": message.id,
        "timestamp": message.timestamp.isoformat()
    }

@router.get("/status/{device_id}")
async def get_device_status(
    device_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get device status and configuration"""
    device = require_device_auth(device_id, token, db)
    
    # Get recent messages
    recent_messages = db.query(Message).filter(
        Message.device_id == device_id
    ).order_by(Message.timestamp.desc()).limit(5).all()
    
    # Get pending commands count
    pending_commands = db.query(Command).filter(
        Command.device_id == device_id,
        Command.status == "pending"
    ).count()
    
    return {
        "device_id": device_id,
        "status": device.status,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "firmware_version": device.firmware_version,
        "pending_commands": pending_commands,
        "recent_messages": [
            {
                "type": msg.type,
                "content": msg.content,
                "severity": msg.severity,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in recent_messages
        ]
    }

@router.post("/heartbeat/{device_id}")
async def device_heartbeat(
    device_id: str,
    status: str = Form("online"),
    firmware_version: str = Form(None),
    ip_address: str = Form(None),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Device heartbeat endpoint"""
    device = require_device_auth(device_id, token, db)
    
    # Update device status
    DeviceManager.update_device_status(
        db, device_id, status, ip_address, firmware_version
    )
    
    return {
        "status": "acknowledged",
        "device_id": device_id,
        "server_time": datetime.utcnow().isoformat()
    }
