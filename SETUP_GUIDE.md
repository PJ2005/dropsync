# 🚀 IoT DropSync - Quick Setup Guide

## 📋 Prerequisites Checklist

- [ ] Raspberry Pi 5 with Raspberry Pi OS
- [ ] ESP8266 development board (NodeMCU, Wemos D1 Mini, etc.)
- [ ] WiFi network for both devices
- [ ] Arduino IDE on development machine
- [ ] USB cable for ESP8266 programming

## 🔧 Step-by-Step Setup

### 1️⃣ Raspberry Pi 5 Setup (5 minutes)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install python3 python3-pip python3-venv git -y

# 3. Clone project
git clone <your-repo> dropsync && cd dropsync

# 4. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure devices
cat > app/device_auth.json << 'EOF'
{
  "esp001": "secure-token-esp001-xyz123",
  "esp002": "secure-token-esp002-abc456"
}
EOF

# 6. Start server
python3 start.py
```

### 2️⃣ ESP8266 Setup (3 minutes)

1. **Install Arduino IDE** and ESP8266 board support
2. **Install ArduinoJson library** via Library Manager
3. **Configure the code** in `esp8266_dropsync.ino`:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   const char* device_id = "esp001";
   const char* auth_token = "secure-token-esp001-xyz123";
   const char* server = "http://192.168.1.100:8000";  // Pi IP
   ```
4. **Upload code** to ESP8266
5. **Monitor serial output** (115200 baud)

### 3️⃣ Testing (2 minutes)

```bash
# Test Pi server
curl http://localhost:8000/health

# Test web dashboard
# Open: http://<pi-ip>:8000/dashboard

# Send test command
curl -X POST "http://<pi-ip>:8000/api/v1/admin/devices/esp001/command" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "command=reboot&priority=1"
```

## 🔍 Quick Reference

### Important URLs
- **Dashboard**: `http://<pi-ip>:8000/dashboard`
- **API Docs**: `http://<pi-ip>:8000/api/v1/docs`
- **Health Check**: `http://<pi-ip>:8000/health`

### Key Files
- **Pi Config**: `app/device_auth.json`
- **ESP8266 Code**: `esp8266_dropsync/esp8266_dropsync.ino`
- **Database**: `app/dropsync.db`

### Common Commands
```bash
# Start server
python3 start.py

# Check server status
curl http://localhost:8000/health

# View server logs
journalctl -u dropsync -f

# Register new device
curl -X POST "http://localhost:8000/api/v1/admin/devices/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "device_id=esp002&name=New Device&device_type=esp8266"
```

## 🚨 Troubleshooting

### Pi Issues
- **Server won't start**: Check `pip install -r requirements.txt`
- **Can't access dashboard**: Check firewall `sudo ufw allow 8000`
- **Database errors**: Delete `app/dropsync.db` and restart

### ESP8266 Issues
- **WiFi won't connect**: Check SSID/password in code
- **Can't reach server**: Verify Pi IP address in code
- **Authentication failed**: Check device_id and auth_token match

### Network Issues
- **Devices can't communicate**: Ensure both on same WiFi network
- **Timeouts**: Check firewall settings on Pi
- **API errors**: Verify Pi server is running and accessible

## 📊 Success Indicators

✅ **Pi Server Running**: Health check returns 200 OK  
✅ **ESP8266 Connected**: Serial output shows WiFi connection  
✅ **Communication Working**: ESP8266 logs show successful API calls  
✅ **Dashboard Active**: Web interface shows connected devices  
✅ **Commands Working**: ESP8266 receives and executes commands  

## 🔧 Production Setup

For production deployment, consider:

1. **Enable Pi service**: `sudo systemctl enable dropsync`
2. **Setup log rotation**: Configure `/etc/logrotate.d/dropsync`
3. **Secure tokens**: Use cryptographically secure tokens
4. **Enable firewall**: `sudo ufw enable && sudo ufw allow 8000`
5. **Regular backups**: Backup database and configuration files

---

**Need help?** Check the full README.md for detailed instructions and troubleshooting.
