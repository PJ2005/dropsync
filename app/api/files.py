from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import os
import json

from ..database import get_db
from ..models import FileSync, SyncPackage
from ..utils import FileManager, SystemLogger
from ..auth import require_device_auth
from ..config import settings

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload/{device_id}")
async def upload_file(
    device_id: str,
    file: UploadFile = File(...),
    token: str = Form(...),
    sync_type: str = Form("upload"),
    db: Session = Depends(get_db)
):
    """Upload a file from a device"""
    device = require_device_auth(device_id, token, db)
    
    # Check file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {list(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create device directory
    device_dir = settings.get_device_upload_dir(device_id)
    filepath = device_dir / file.filename
    
    # Save file
    try:
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Track file sync
        file_sync = FileManager.track_file_sync(
            db, device_id, file.filename, str(filepath), sync_type
        )
        
        # Mark as completed
        file_sync.status = "completed"
        file_sync.completed_at = datetime.utcnow()
        db.commit()
        
        SystemLogger.log_event(
            db, "file_uploaded", device_id,
            f"File '{file.filename}' uploaded from device {device_id}"
        )
        
        return {
            "status": "uploaded",
            "device_id": device_id,
            "filename": file.filename,
            "size": file.size,
            "sync_id": file_sync.id
        }
    
    except Exception as e:
        SystemLogger.log_event(
            db, "file_upload_error", device_id,
            f"Failed to upload file '{file.filename}': {str(e)}",
            "error"
        )
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/list/{device_id}")
async def list_device_files(
    device_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """List files for a device"""
    device = require_device_auth(device_id, token, db)
    
    files = FileManager.get_device_files(settings.UPLOAD_DIR, device_id)
    
    return {
        "device_id": device_id,
        "file_count": len(files),
        "files": files
    }

@router.get("/sync-packages/{device_id}")
async def get_sync_packages(
    device_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get available sync packages for a device"""
    device = require_device_auth(device_id, token, db)
    
    packages = db.query(SyncPackage).filter(
        SyncPackage.target_device_id == device_id,
        SyncPackage.status == "staged"
    ).all()
    
    return {
        "device_id": device_id,
        "packages": [
            {
                "id": pkg.id,
                "name": pkg.package_name,
                "type": pkg.package_type,
                "file_count": pkg.file_count,
                "size": pkg.total_size,
                "created_at": pkg.created_at.isoformat(),
                "description": pkg.description
            }
            for pkg in packages
        ]
    }

@router.post("/sync-packages/{device_id}/{package_id}/download")
async def download_sync_package(
    device_id: str,
    package_id: int,
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Mark a sync package as downloaded by device"""
    device = require_device_auth(device_id, token, db)
    
    package = db.query(SyncPackage).filter(
        SyncPackage.id == package_id,
        SyncPackage.target_device_id == device_id
    ).first()
    
    if not package:
        raise HTTPException(status_code=404, detail="Sync package not found")
    
    package.status = "deployed"
    package.deployed_at = datetime.utcnow()
    db.commit()
    
    SystemLogger.log_event(
        db, "package_deployed", device_id,
        f"Sync package '{package.package_name}' deployed to device {device_id}"
    )
    
    return {
        "status": "deployed",
        "package_id": package_id,
        "package_name": package.package_name
    }

@router.get("/sync-history/{device_id}")
async def get_sync_history(
    device_id: str,
    token: str = Query(...),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get file sync history for a device"""
    device = require_device_auth(device_id, token, db)
    
    syncs = db.query(FileSync).filter(
        FileSync.device_id == device_id
    ).order_by(FileSync.timestamp.desc()).limit(limit).all()
    
    return {
        "device_id": device_id,
        "sync_history": [
            {
                "id": sync.id,
                "filename": sync.filename,
                "sync_type": sync.sync_type,
                "status": sync.status,
                "size": sync.file_size,
                "timestamp": sync.timestamp.isoformat(),
                "completed_at": sync.completed_at.isoformat() if sync.completed_at else None
            }
            for sync in syncs
        ]
    }

@router.delete("/files/{device_id}/{filename}")
async def delete_file(
    device_id: str,
    filename: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """Delete a file from device storage"""
    device = require_device_auth(device_id, token, db)
    
    device_dir = settings.get_device_upload_dir(device_id)
    filepath = device_dir / filename
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(filepath)
        
        # Track deletion
        FileManager.track_file_sync(
            db, device_id, filename, str(filepath), "delete"
        )
        
        SystemLogger.log_event(
            db, "file_deleted", device_id,
            f"File '{filename}' deleted from device {device_id}"
        )
        
        return {"status": "deleted", "filename": filename}
    
    except Exception as e:
        SystemLogger.log_event(
            db, "file_delete_error", device_id,
            f"Failed to delete file '{filename}': {str(e)}",
            "error"
        )
        raise HTTPException(status_code=500, detail="File deletion failed")
