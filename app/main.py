from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path
import os
import json

# Import our modules
from .config import settings
from .database import init_database, get_db
from .models import Device, Command, Message, FileSync, SyncPackage
from .utils import DeviceManager, CommandManager, FileManager, SystemLogger
from .auth import auth_manager
from .api.device import router as device_router
from .api.files import router as files_router
from .api.admin import router as admin_router

# Initialize settings and create directories
settings.create_directories()

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_database()

# Setup templates
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

# Include API routers
app.include_router(device_router, prefix=settings.API_V1_PREFIX)
app.include_router(files_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)

# Legacy compatibility endpoints
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Web dashboard for monitoring and control"""
    # Get system statistics
    devices = DeviceManager.get_active_devices(db)
    online_devices = [d for d in devices if DeviceManager.is_device_online(d)]
    
    # Get recent messages
    messages = db.query(Message).order_by(Message.timestamp.desc()).limit(20).all()
    
    # Get recent commands
    commands = db.query(Command).order_by(Command.timestamp.desc()).limit(20).all()
    
    # Get recent file syncs
    file_syncs = db.query(FileSync).order_by(FileSync.timestamp.desc()).limit(10).all()
    
    # Get sync packages
    sync_packages = db.query(SyncPackage).order_by(SyncPackage.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "devices": devices,
        "online_devices": online_devices,
        "messages": messages,
        "commands": commands,
        "file_syncs": file_syncs,
        "sync_packages": sync_packages,
        "stats": {
            "total_devices": len(devices),
            "online_devices": len(online_devices),
            "pending_commands": len([c for c in commands if c.status == "pending"]),
            "recent_messages": len(messages)
        }
    })

@app.post("/upload/{device_id}")
async def upload_file_legacy(
    device_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Legacy file upload endpoint (for backward compatibility)"""
    # Create device directory
    device_dir = settings.get_device_upload_dir(device_id)
    filepath = device_dir / file.filename
    
    # Save file
    with open(filepath, "wb") as f:
        f.write(await file.read())
    
    # Track file sync
    FileManager.track_file_sync(db, device_id, file.filename, str(filepath))
    
    SystemLogger.log_event(
        db, "file_uploaded", device_id,
        f"File '{file.filename}' uploaded from device {device_id} (legacy endpoint)"
    )
    
    return {"status": "uploaded", "device": device_id, "file": file.filename}

@app.post("/send-command/{device_id}")
async def send_command_legacy(
    device_id: str,
    command: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Legacy command sending endpoint"""
    # Verify token
    if not auth_manager.verify_device_token(device_id, token, db):
        raise HTTPException(status_code=403, detail="Unauthorized device or token")
    
    # Send command
    cmd = CommandManager.send_command(db, device_id, command)
    
    return {"status": "queued", "command": command, "command_id": cmd.id}

@app.get("/message/{device_id}")
async def get_command_legacy(
    device_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Legacy command retrieval endpoint"""
    # Verify token
    if not auth_manager.verify_device_token(device_id, token, db):
        raise HTTPException(status_code=403, detail="Unauthorized device or token")
    
    # Get next command
    cmd = CommandManager.get_next_command(db, device_id)
    
    if cmd:
        # Mark as sent
        CommandManager.mark_command_sent(db, cmd.id)
        return {"command": cmd.command, "command_id": cmd.id}
    
    return {"command": "none"}

@app.post("/message")
async def post_message_legacy(
    device_id: str = Form(...),
    msg_type: str = Form(...),
    content: str = Form(...),
    token: str = Form(...),
    db: Session = Depends(get_db)
):
    """Legacy message posting endpoint"""
    # Verify token
    if not auth_manager.verify_device_token(device_id, token, db):
        raise HTTPException(status_code=403, detail="Unauthorized device or token")
    
    # Update device status
    DeviceManager.update_device_status(db, device_id, "online")
    
    # Log message
    SystemLogger.log_device_message(db, device_id, msg_type, content)
    
    return {"status": "logged"}

@app.get("/check-files/{device_id}")
async def check_files_legacy(
    device_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Legacy file checking endpoint"""
    # Verify token
    if not auth_manager.verify_device_token(device_id, token, db):
        raise HTTPException(status_code=403, detail="Unauthorized device or token")
    
    files = FileManager.get_device_files(settings.UPLOAD_DIR, device_id)
    return {"file_count": len(files)}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "status": "online",
        "endpoints": {
            "dashboard": "/dashboard",
            "api_docs": f"{settings.API_V1_PREFIX}/docs",
            "api_v1": settings.API_V1_PREFIX
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = "error"
    
    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

# Mount static files
if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Dashboard available at: http://{settings.HOST}:{settings.PORT}/dashboard")
    print(f"API documentation at: http://{settings.HOST}:{settings.PORT}{settings.API_V1_PREFIX}/docs")
    
    # Log startup
    from .database import SessionLocal
    db = SessionLocal()
    try:
        SystemLogger.log_event(
            db, "system_startup", "system",
            f"{settings.PROJECT_NAME} v{settings.VERSION} started"
        )
    except Exception as e:
        print(f"Failed to log startup event: {e}")
    finally:
        db.close()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    print(f"Shutting down {settings.PROJECT_NAME}")
    
    # Log shutdown
    from .database import SessionLocal
    db = SessionLocal()
    try:
        SystemLogger.log_event(
            db, "system_shutdown", "system",
            f"{settings.PROJECT_NAME} v{settings.VERSION} shutting down"
        )
    except Exception as e:
        print(f"Failed to log shutdown event: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
