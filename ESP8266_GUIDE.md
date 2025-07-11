# ESP8266 Configuration Guide

## 🔧 Quick ESP8266 Setup

### 1. Arduino IDE Setup
1. **Install Arduino IDE** from https://www.arduino.cc/en/software
2. **Add ESP8266 Board Support**:
   - Go to File → Preferences
   - Add this URL to "Additional Boards Manager URLs":
     ```
     http://arduino.esp8266.com/stable/package_esp8266com_index.json
     ```
   - Go to Tools → Board → Boards Manager
   - Search for "esp8266" and install "ESP8266 by ESP8266 Community"

3. **Install Required Libraries**:
   - Go to Sketch → Include Library → Manage Libraries
   - Search and install: "ArduinoJson" by Benoit Blanchon

### 2. Hardware Setup
- **ESP8266 Development Board** (NodeMCU, Wemos D1 Mini, etc.)
- **USB Cable** for programming
- **Power Supply** (USB or external)

### 3. Code Configuration

Open `esp8266_dropsync/esp8266_dropsync.ino` and update these values:

```cpp
// WiFi Configuration - REQUIRED
const char* ssid = "YOUR_WIFI_SSID";           // Your WiFi network name
const char* password = "YOUR_WIFI_PASSWORD";   // Your WiFi password

// Device Configuration - REQUIRED
const char* device_id = "esp001";                        // Unique device ID
const char* auth_token = "secure-token-esp001-xyz123";   // Must match Pi config

// Server Configuration - REQUIRED
const char* server = "http://192.168.1.100:8000";       // Your Raspberry Pi IP
```

### 4. Upload Process
1. **Connect ESP8266** to computer via USB
2. **Select Board**: Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)
3. **Select Port**: Tools → Port → COM3 (Windows) or /dev/ttyUSB0 (Linux)
4. **Upload Code**: Click the upload button (→)
5. **Monitor Serial**: Tools → Serial Monitor (set to 115200 baud)

### 5. Expected Serial Output
```
Starting ESP8266 DropSync Client...
Device ID: esp001
Firmware: 1.2.0
Connecting to WiFi: YOUR_WIFI_SSID
WiFi connected successfully
IP address: 192.168.1.101
Server: http://192.168.1.100:8000
Registering device...
Device registered successfully
Starting main loop...
Polling for commands...
```

## 🔧 Multiple Device Setup

### Device 1 (esp001)
```cpp
const char* device_id = "esp001";
const char* auth_token = "secure-token-esp001-xyz123";
```

### Device 2 (esp002)
```cpp
const char* device_id = "esp002";
const char* auth_token = "secure-token-esp002-abc456";
```

### Device 3 (esp003)
```cpp
const char* device_id = "esp003";
const char* auth_token = "secure-token-esp003-def789";
```

**Note**: Each device needs a unique device_id and matching auth_token in the Pi's `device_auth.json` file.

## 📊 Monitoring ESP8266

### Serial Monitor Output
Monitor these key indicators:
- ✅ **WiFi Connected**: Shows IP address
- ✅ **Server Reachable**: Successful HTTP requests
- ✅ **Authentication OK**: Device registration success
- ✅ **Command Polling**: Regular polling messages
- ✅ **Command Execution**: Command received and executed

### Common Serial Messages
```
[INFO] WiFi connected: 192.168.1.101
[INFO] Device registered successfully
[INFO] Polling for commands...
[INFO] Command received: reboot
[INFO] Executing command: reboot
[INFO] Command completed successfully
[INFO] Heartbeat sent
```

## 🚨 Troubleshooting

### WiFi Connection Issues
```cpp
// Check WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";      // Case sensitive!
const char* password = "YOUR_WIFI_PASSWORD";
```

### Server Connection Issues
```cpp
// Verify Pi IP address
const char* server = "http://192.168.1.100:8000";  // Check Pi IP with: ip addr show
```

### Authentication Issues
```cpp
// Check device ID and token match Pi configuration
const char* device_id = "esp001";
const char* auth_token = "secure-token-esp001-xyz123";  // Must match device_auth.json
```

### Upload Issues
- **Board not detected**: Check USB cable and drivers
- **Upload fails**: Try different USB port or cable
- **Compilation errors**: Check board selection and library installation

## 🔧 Advanced Configuration

### Custom Timing
```cpp
unsigned long poll_interval = 10000;      // Command polling (10 seconds)
unsigned long heartbeat_interval = 30000; // Heartbeat (30 seconds)
unsigned long retry_delay = 5000;         // Retry delay (5 seconds)
```

### Debug Mode
```cpp
#define DEBUG_MODE 1  // Enable debug output

// Add this to setup() for detailed debugging
Serial.setDebugOutput(true);
```

### Power Management
```cpp
// Enable deep sleep (optional)
#include <ESP8266WiFi.h>

// Sleep for 1 minute between polls
ESP.deepSleep(60 * 1000000);  // microseconds
```

## 📋 Testing Commands

Once ESP8266 is connected, test these commands from the Pi dashboard:

1. **reboot** - Restart ESP8266
2. **status** - Get device status
3. **sync** - Trigger file sync
4. **upload-log** - Upload log file
5. **ping** - Connectivity test

## 🎯 Success Checklist

- [ ] ESP8266 connects to WiFi
- [ ] ESP8266 registers with Pi server
- [ ] Regular polling messages in serial monitor
- [ ] Commands sent from Pi are received and executed
- [ ] Device appears as "online" in Pi dashboard
- [ ] Heartbeat messages sent successfully

---

For more detailed information, see the main README.md file.
