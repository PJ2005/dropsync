# 🚀 IoT DropSync - Secure Local File Transfer & Command Relay

**Offline IoT Sync Node for Secure Field Deployment**

A comprehensive system for field-deployed IoT nodes (ESP8266/ESP32) that need to securely sync updates, logs, and commands with a local hub (Raspberry Pi) without internet connectivity.

## 🎯 Use Case

Perfect for scenarios where edge devices need to:
- ✅ Securely sync updates and logs with a local "hub" 
- ✅ Operate fully offline (no cloud dependency)
- ✅ Receive batch instructions (firmware triggers, task scripts)
- ✅ Report status and diagnostics back to the hub
- ✅ Work in areas without internet (factories, disaster zones, rural deployments)

## 🏗️ Architecture

```
┌─────────────────┐    WiFi/Local Network    ┌─────────────────┐
│   ESP8266/32    │◄──────────────────────►│  Raspberry Pi   │
│  (Edge Nodes)   │     Secure Auth          │   (Hub Server)  │
│                 │                          │                 │
│ • File Upload   │                          │ • FastAPI Web   │
│ • Command Poll  │                          │ • SQLite DB     │
│ • Status Report │                          │ • Web Dashboard │
│ • Retry Logic   │                          │ • File Storage  │
└─────────────────┘                          └─────────────────┘
```

## 🌟 Features

### 🖥️ Hub Server (Raspberry Pi - FastAPI)
- **Authenticated API**: Token-based device whitelist
- **File Staging**: Upload "sync packages" tagged with device IDs
- **Command Queue**: Send targeted instructions to specific devices
- **Message Log**: Timestamped logs with device ID and actions
- **SQLite Database**: Persistent storage for commands, messages, and file history
- **Web Dashboard**: Real-time monitoring and control interface
- **RESTful API**: Comprehensive API with automatic documentation

### 📡 Edge Devices (ESP8266/ESP32)
- **Unique Device ID**: MAC address-based identification
- **Secure Polling**: GET requests to device-specific message queue
- **Command Processing**: Handle reboot, sync, upload-log, and custom commands
- **File Operations**: Simulate log uploads back to hub
- **Retry Logic**: Automatic retry for communication failures
- **Authentication**: Pre-shared token in every request

## 🚀 Complete Setup Guide: Raspberry Pi 5 + ESP8266

### 📟 Part 1: Raspberry Pi 5 Setup (Hub Server)

#### 1.1 Initial Pi Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install additional system dependencies
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
```

#### 1.2 Clone and Setup Project
```bash
# Clone your project (or transfer files)
git clone <your-repo-url> dropsync
# OR if transferring files:
# scp -r /path/to/dropsync pi@<pi-ip>:~/

cd dropsync

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 1.3 Configure Network Settings
```bash
# Find Pi's IP address
ip addr show | grep "inet " | grep -v 127.0.0.1

# Note down the IP (e.g., 192.168.1.100) - you'll need this for ESP8266
```

#### 1.4 Configure the Application
```bash
# Create device auth file
cat > app/device_auth.json << 'EOF'
{
  "esp001": "secure-token-esp001-xyz123",
  "esp002": "secure-token-esp002-abc456",
  "esp003": "secure-token-esp003-def789"
}
EOF

# Set environment variables (optional)
export SECRET_KEY="your-super-secret-key-here"
export HOST="0.0.0.0"
export PORT="8000"
```

#### 1.5 Start the Server
```bash
# Method 1: Using the startup script
python3 start.py

# Method 2: Direct start
cd app
python3 main.py

# Method 3: Production with Gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

#### 1.6 Verify Server is Running
```bash
# Check if server is running
curl http://localhost:8000/health

# Check API documentation
# Open browser: http://<pi-ip>:8000/api/v1/docs
# Dashboard: http://<pi-ip>:8000/dashboard
```

#### 1.7 Setup as System Service (Optional)
```bash
# Create systemd service
sudo tee /etc/systemd/system/dropsync.service << 'EOF'
[Unit]
Description=IoT DropSync Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/dropsync
Environment=PATH=/home/pi/dropsync/venv/bin
ExecStart=/home/pi/dropsync/venv/bin/python /home/pi/dropsync/app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable dropsync
sudo systemctl start dropsync

# Check status
sudo systemctl status dropsync
```

### 🔌 Part 2: ESP8266 Setup (Edge Devices)

#### 2.1 Arduino IDE Setup
```bash
# Install Arduino IDE on your development machine
# Download from: https://www.arduino.cc/en/software

# In Arduino IDE:
# 1. Go to File → Preferences
# 2. Add ESP8266 board URL: http://arduino.esp8266.com/stable/package_esp8266com_index.json
# 3. Go to Tools → Board → Boards Manager
# 4. Search "esp8266" and install "ESP8266 by ESP8266 Community"
```

#### 2.2 Install Required Libraries
```bash
# In Arduino IDE, go to Sketch → Include Library → Manage Libraries
# Install these libraries:
# - ESP8266WiFi (built-in)
# - ESP8266HTTPClient (built-in)
# - ArduinoJson (by Benoit Blanchon)
```

#### 2.3 Configure ESP8266 Code
1. Open `esp8266_dropsync/esp8266_dropsync.ino` in Arduino IDE
2. Update these configuration values:

```cpp
// WiFi Configuration - UPDATE THESE VALUES
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Device Configuration - UPDATE THESE VALUES
const char* device_id = "esp001";  // Must match device_auth.json on Pi
const char* auth_token = "secure-token-esp001-xyz123";  // Must match device_auth.json

// Server Configuration - UPDATE WITH YOUR RASPBERRY PI IP
const char* server = "http://192.168.1.100:8000";  // Replace with your Pi's IP
```

#### 2.4 Upload Code to ESP8266
1. Connect ESP8266 to your computer via USB
2. Select correct board: Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)
3. Select correct port: Tools → Port → COMx (Windows) or /dev/ttyUSBx (Linux)
4. Click Upload button

#### 2.5 Monitor ESP8266 Serial Output
1. Open Serial Monitor: Tools → Serial Monitor
2. Set baud rate to 115200
3. You should see connection and polling messages

### 🧪 Part 3: Testing the System

#### 3.1 Test Pi Server
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test device registration (from Pi)
curl -X POST "http://localhost:8000/api/v1/admin/devices/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_id=esp001&name=Test ESP&device_type=esp8266"
```

#### 3.2 Test ESP8266 Connectivity
1. Power on ESP8266 - it should connect to WiFi
2. Check Pi server logs for device connection
3. Check ESP8266 serial output for successful API calls

#### 3.3 Test Command Sending
```bash
# Send command to ESP8266 (from Pi or any computer on network)
curl -X POST "http://<pi-ip>:8000/api/v1/admin/devices/esp001/command" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=reboot&priority=1"

# Check ESP8266 serial output - it should receive and execute the command
```

#### 3.4 Test Web Dashboard
1. Open browser: `http://<pi-ip>:8000/dashboard`
2. You should see connected devices and system status
3. Try sending commands through the web interface

### 🔧 Part 4: Troubleshooting

#### 4.1 Common Pi Issues
```bash
# Check server logs
journalctl -u dropsync -f

# Check if port is open
sudo netstat -tulpn | grep :8000

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 8000
```

#### 4.2 Common ESP8266 Issues
```cpp
// Add debug prints to ESP8266 code:
Serial.begin(115200);
Serial.println("Starting ESP8266...");

// Check WiFi connection
if (WiFi.status() == WL_CONNECTED) {
  Serial.println("WiFi connected successfully");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
} else {
  Serial.println("WiFi connection failed");
}
```

#### 4.3 Network Issues
```bash
# Ping test from ESP8266 network to Pi
ping <pi-ip>

# Check if devices are on same network
ip route show

# Test HTTP connectivity
curl -v http://<pi-ip>:8000/health
```

### 📊 Part 5: Production Considerations

#### 5.1 Security Hardening
```bash
# Change default tokens
# Edit app/device_auth.json with secure tokens

# Use environment variables for secrets
export SECRET_KEY="$(openssl rand -hex 32)"

# Enable firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8000
```

#### 5.2 Monitoring and Logging
```bash
# Setup log rotation
sudo tee /etc/logrotate.d/dropsync << 'EOF'
/home/pi/dropsync/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
EOF
```

#### 5.3 Backup Strategy
```bash
# Backup database
cp app/dropsync.db app/dropsync.db.backup

# Backup configuration
tar -czf dropsync-config-$(date +%Y%m%d).tar.gz app/device_auth.json app/config.py
```

## 🚀 Quick Start

### 1. Set up the Hub Server

```bash
# Clone the repository
git clone <your-repo-url>
cd dropsync

# Install dependencies
pip install -r requirements.txt

# Start the server
cd app
python main.py
```

The server will start on `http://localhost:8000`

### 2. Access the Dashboard

Open your browser and go to:
- **Dashboard**: `http://localhost:8000/dashboard`
- **API Documentation**: `http://localhost:8000/api/v1/docs`

### 3. Configure ESP8266 Device

1. Update the Arduino code with your WiFi credentials
2. Set the correct hub IP address
3. Configure unique device ID and auth token
4. Upload to your ESP8266

```cpp
const char* ssid = "Your_WiFi_SSID";
const char* password = "Your_WiFi_Password";
const char* device_id = "esp001";
const char* auth_token = "your-secure-token";
const char* server = "http://192.168.1.100:8000";
```

## 📁 Project Structure

```
dropsync/
├── app/
│   ├── main.py              # Main FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models.py            # Database models
│   ├── database.py          # Database initialization
│   ├── utils.py             # Utility functions and managers
│   ├── auth.py              # Authentication and security
│   ├── api/
│   │   ├── device.py        # Device API endpoints
│   │   ├── files.py         # File management endpoints
│   │   └── admin.py         # Admin management endpoints
│   ├── uploads/             # File storage directory
│   └── device_auth.json     # Device authentication tokens
├── templates/
│   └── dashboard.html       # Web dashboard template
├── esp8266_dropsync/
│   └── esp8266_dropsync.ino # Arduino code for ESP8266
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 API Endpoints

### Device Management
- `GET /api/v1/device/ping/{device_id}` - Device connectivity check
- `GET /api/v1/device/commands/{device_id}` - Get pending commands
- `POST /api/v1/device/commands/{device_id}/complete` - Mark command as completed
- `POST /api/v1/device/messages/{device_id}` - Send message from device
- `GET /api/v1/device/status/{device_id}` - Get device status
- `POST /api/v1/device/heartbeat/{device_id}` - Device heartbeat

### File Management
- `POST /api/v1/files/upload/{device_id}` - Upload file from device
- `GET /api/v1/files/list/{device_id}` - List device files
- `GET /api/v1/files/sync-packages/{device_id}` - Get sync packages
- `GET /api/v1/files/sync-history/{device_id}` - Get sync history
- `DELETE /api/v1/files/files/{device_id}/{filename}` - Delete file

### Admin Management
- `GET /api/v1/admin/devices` - List all devices
- `POST /api/v1/admin/devices/register` - Register new device
- `POST /api/v1/admin/devices/{device_id}/command` - Send command
- `GET /api/v1/admin/devices/{device_id}/commands` - Get command history
- `GET /api/v1/admin/devices/{device_id}/messages` - Get device messages
- `GET /api/v1/admin/system/stats` - Get system statistics

## 🛠️ Configuration

### Environment Variables
```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./dropsync.db
```

### Device Authentication
Edit `app/device_auth.json` to add new devices:
```json
{
  "esp001": "secure-token-1",
  "esp002": "secure-token-2",
  "esp003": "secure-token-3"
}
```

## 🔒 Security Features

- **Token-based Authentication**: Each device has a unique auth token
- **Rate Limiting**: Prevents API abuse
- **Input Validation**: Comprehensive input sanitization
- **File Type Restrictions**: Only allowed file types can be uploaded
- **Device Whitelisting**: Only registered devices can connect
- **Secure Token Generation**: Cryptographically secure token generation

## 📊 Database Schema

The system uses SQLite with the following main tables:
- **devices**: Device registration and status
- **commands**: Command queue and execution history
- **messages**: Device messages and logs
- **file_syncs**: File sync operations tracking
- **sync_packages**: Staged file packages for deployment
- **system_logs**: System-wide event logging

## 🎨 Dashboard Features

- **Real-time Monitoring**: Live device status and statistics
- **Device Management**: View and control connected devices
- **Command Control**: Send commands to specific devices
- **File Management**: Upload files and manage sync packages
- **Activity Logs**: View recent commands, messages, and file operations
- **Modern UI**: Responsive design with glassmorphism effects
- **Auto-refresh**: Automatic dashboard updates every 30 seconds

## 🔄 Development Workflow

1. **Start Development Server**:
   ```bash
   cd app
   python main.py
   ```

2. **View API Documentation**:
   Visit `http://localhost:8000/api/v1/docs` for interactive API docs

3. **Monitor Logs**:
   Check console output for system events and errors

4. **Test with ESP8266**:
   Use the provided Arduino code to test device connectivity

## 🚀 Deployment

### Production Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000

# Or run directly
python app/main.py
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app/main.py"]
```

## 📈 Performance & Scalability

- **Lightweight**: SQLite database for minimal resource usage
- **Efficient**: Async FastAPI for high performance
- **Scalable**: Modular architecture supports multiple devices
- **Reliable**: Comprehensive error handling and retry logic
- **Monitoring**: Built-in health checks and system statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for database management
- ESP8266 Arduino Core for microcontroller support

---

**Perfect for**: IoT deployments, edge computing, offline systems, field operations, industrial automation, disaster response, and any scenario requiring secure local device communication without internet dependency.