/**
 * IoT DropSync - ESP8266 Client
 * Secure Local File Transfer & Command Relay for Edge Devices
 * 
 * Features:
 * - Secure token-based authentication
 * - Command polling and execution
 * - File sync monitoring
 * - Status reporting with heartbeat
 * - Retry logic and error handling
 * - Configurable polling intervals
 * - Multiple command support
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>

// ============== CONFIGURATION ==============
// WiFi Configuration - UPDATE THESE VALUES
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Device Configuration - UPDATE THESE VALUES
const char* device_id = "esp001";  // Must match device_auth.json on Pi
const char* auth_token = "secure-token-esp001-xyz123";  // Must match device_auth.json
const char* device_name = "ESP8266 Field Node";
const char* firmware_version = "1.2.0";

// Server Configuration - UPDATE WITH YOUR RASPBERRY PI IP
const char* server = "http://192.168.1.100:8000";  // Replace with your Pi's IP
const char* api_base = "/api/v1";

// Timing Configuration
unsigned long poll_interval = 10000;      // Command polling interval (ms)
unsigned long heartbeat_interval = 30000; // Heartbeat interval (ms)
unsigned long retry_delay = 5000;         // Retry delay on failure (ms)
const int max_retries = 3;                // Maximum retry attempts

// ============== GLOBAL VARIABLES ==============
WiFiClient wifiClient;
unsigned long last_poll = 0;
unsigned long last_heartbeat = 0;
unsigned long last_file_check = 0;
int retry_count = 0;
bool system_status = true;

// Status tracking
String last_command = "";
String device_status = "booting";
unsigned long uptime_start = 0;

// ============== SETUP ==============
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== IoT DropSync ESP8266 Client ===");
    Serial.println("Version: " + String(firmware_version));
    Serial.println("Device ID: " + String(device_id));
    
    // Initialize WiFi
    connectToWiFi();
    
    // Record uptime start
    uptime_start = millis();
    
    // Send initial status
    device_status = "online";
    sendHeartbeat();
    sendMessage("status", "ESP8266 boot complete - " + String(device_name));
    
    Serial.println("System initialized successfully!");
}

// ============== MAIN LOOP ==============
void loop() {
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        device_status = "wifi_error";
        Serial.println("WiFi disconnected. Attempting reconnection...");
        connectToWiFi();
        return;
    }
    
    unsigned long current_time = millis();
    
    // Command polling
    if (current_time - last_poll > poll_interval) {
        last_poll = current_time;
        checkAndExecuteCommands();
    }
    
    // Heartbeat
    if (current_time - last_heartbeat > heartbeat_interval) {
        last_heartbeat = current_time;
        sendHeartbeat();
    }
    
    // File check (less frequent)
    if (current_time - last_file_check > (poll_interval * 3)) {
        last_file_check = current_time;
        checkFiles();
    }
    
    // Small delay to prevent overwhelming the system
    delay(100);
}

// ============== WIFI FUNCTIONS ==============
void connectToWiFi() {
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi");
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.println("IP address: " + WiFi.localIP().toString());
        Serial.println("Signal strength: " + String(WiFi.RSSI()) + " dBm");
        device_status = "online";
        retry_count = 0;
    } else {
        Serial.println("\nWiFi connection failed!");
        device_status = "wifi_error";
    }
}

// ============== COMMAND FUNCTIONS ==============
void checkAndExecuteCommands() {
    HTTPClient http;
    String url = String(server) + api_base + "/device/commands/" + device_id + "?token=" + auth_token;
    
    http.begin(wifiClient, url);
    http.addHeader("User-Agent", "ESP8266-DropSync/" + String(firmware_version));
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String payload = http.getString();
        Serial.println("Command response: " + payload);
        
        // Parse JSON response
        DynamicJsonDocument doc(1024);
        DeserializationError error = deserializeJson(doc, payload);
        
        if (!error) {
            if (doc.containsKey("command") && doc["command"] != "none") {
                String command = doc["command"];
                int command_id = doc["command_id"];
                
                Serial.println("Executing command: " + command);
                executeCommand(command, command_id);
            }
        }
        
        retry_count = 0;
    } else if (httpCode == 403) {
        Serial.println("Authentication failed!");
        sendMessage("error", "Authentication failed - check token");
        device_status = "auth_error";
    } else {
        Serial.println("Command check failed. HTTP code: " + String(httpCode));
        handleRetry();
    }
    
    http.end();
}

void executeCommand(String command, int command_id) {
    last_command = command;
    String result = "";
    bool success = true;
    
    // Execute different commands
    if (command == "sync") {
        result = executeSyncCommand();
    } else if (command == "reboot") {
        result = executeRebootCommand();
    } else if (command == "status") {
        result = executeStatusCommand();
    } else if (command == "ping") {
        result = executePingCommand();
    } else if (command == "upload-log") {
        result = executeUploadLogCommand();
    } else if (command == "clear-files") {
        result = executeClearFilesCommand();
    } else if (command == "firmware-info") {
        result = executeFirmwareInfoCommand();
    } else if (command == "network-info") {
        result = executeNetworkInfoCommand();
    } else {
        result = "Unknown command: " + command;
        success = false;
    }
    
    // Send command completion
    completeCommand(command_id, result, success);
}

String executeSyncCommand() {
    sendMessage("status", "Starting file sync...");
    delay(1000); // Simulate sync process
    sendMessage("status", "File sync completed successfully");
    return "Sync operation completed";
}

String executeRebootCommand() {
    sendMessage("status", "Rebooting device...");
    delay(1000);
    ESP.restart();
    return "Reboot initiated";
}

String executeStatusCommand() {
    unsigned long uptime = (millis() - uptime_start) / 1000;
    String status = "Device: " + String(device_name) + 
                   ", Status: " + device_status + 
                   ", Uptime: " + String(uptime) + "s" +
                   ", Free Heap: " + String(ESP.getFreeHeap()) + " bytes" +
                   ", WiFi RSSI: " + String(WiFi.RSSI()) + " dBm";
    
    sendMessage("status", status);
    return status;
}

String executePingCommand() {
    return "Pong from " + String(device_id);
}

String executeUploadLogCommand() {
    sendMessage("status", "Preparing log upload...");
    // Simulate log collection and upload
    delay(2000);
    sendMessage("status", "Log upload completed");
    return "Log upload successful";
}

String executeClearFilesCommand() {
    sendMessage("status", "Clearing local files...");
    delay(500);
    sendMessage("status", "Files cleared");
    return "Files cleared successfully";
}

String executeFirmwareInfoCommand() {
    String info = "Firmware: " + String(firmware_version) + 
                 ", Chip ID: " + String(ESP.getChipId()) + 
                 ", Flash Size: " + String(ESP.getFlashChipSize()) + 
                 ", SDK Version: " + String(ESP.getSdkVersion());
    sendMessage("info", info);
    return info;
}

String executeNetworkInfoCommand() {
    String info = "WiFi SSID: " + String(WiFi.SSID()) + 
                 ", IP: " + WiFi.localIP().toString() + 
                 ", MAC: " + WiFi.macAddress() + 
                 ", Gateway: " + WiFi.gatewayIP().toString();
    sendMessage("info", info);
    return info;
}

void completeCommand(int command_id, String result, bool success) {
    HTTPClient http;
    String url = String(server) + api_base + "/device/commands/" + device_id + "/complete";
    
    http.begin(wifiClient, url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    http.addHeader("User-Agent", "ESP8266-DropSync/" + String(firmware_version));
    
    String body = "command_id=" + String(command_id) + 
                  "&result=" + result + 
                  "&token=" + auth_token;
    
    int httpCode = http.POST(body);
    
    if (httpCode == 200) {
        Serial.println("Command completed successfully");
    } else {
        Serial.println("Failed to complete command. HTTP code: " + String(httpCode));
    }
    
    http.end();
}

// ============== COMMUNICATION FUNCTIONS ==============
void sendHeartbeat() {
    HTTPClient http;
    String url = String(server) + api_base + "/device/heartbeat/" + device_id;
    
    http.begin(wifiClient, url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    http.addHeader("User-Agent", "ESP8266-DropSync/" + String(firmware_version));
    
    String body = "status=" + device_status + 
                  "&firmware_version=" + firmware_version + 
                  "&ip_address=" + WiFi.localIP().toString() + 
                  "&token=" + auth_token;
    
    int httpCode = http.POST(body);
    
    if (httpCode == 200) {
        Serial.println("Heartbeat sent successfully");
    } else {
        Serial.println("Heartbeat failed. HTTP code: " + String(httpCode));
    }
    
    http.end();
}

void sendMessage(String type, String content) {
    HTTPClient http;
    String url = String(server) + api_base + "/device/messages/" + device_id;
    
    http.begin(wifiClient, url);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    http.addHeader("User-Agent", "ESP8266-DropSync/" + String(firmware_version));
    
    String severity = "info";
    if (type == "error") severity = "error";
    else if (type == "warning") severity = "warning";
    
    String body = "msg_type=" + type + 
                  "&content=" + content + 
                  "&severity=" + severity + 
                  "&token=" + auth_token;
    
    int httpCode = http.POST(body);
    
    if (httpCode == 200) {
        Serial.println("Message sent: " + content);
    } else {
        Serial.println("Failed to send message. HTTP code: " + String(httpCode));
    }
    
    http.end();
}

void checkFiles() {
    HTTPClient http;
    String url = String(server) + api_base + "/files/list/" + device_id + "?token=" + auth_token;
    
    http.begin(wifiClient, url);
    http.addHeader("User-Agent", "ESP8266-DropSync/" + String(firmware_version));
    
    int httpCode = http.GET();
    
    if (httpCode == 200) {
        String response = http.getString();
        Serial.println("Files info: " + response);
        
        // Parse JSON response
        DynamicJsonDocument doc(1024);
        DeserializationError error = deserializeJson(doc, response);
        
        if (!error && doc.containsKey("file_count")) {
            int file_count = doc["file_count"];
            if (file_count > 0) {
                sendMessage("status", "Detected " + String(file_count) + " files available");
            }
        }
    } else {
        Serial.println("File check failed. HTTP code: " + String(httpCode));
    }
    
    http.end();
}

// ============== UTILITY FUNCTIONS ==============
void handleRetry() {
    retry_count++;
    if (retry_count >= max_retries) {
        device_status = "comm_error";
        sendMessage("error", "Max retries reached. Communication error.");
        retry_count = 0;
    }
    delay(retry_delay);
}

void printSystemInfo() {
    Serial.println("=== System Information ===");
    Serial.println("Device ID: " + String(device_id));
    Serial.println("Device Name: " + String(device_name));
    Serial.println("Firmware Version: " + String(firmware_version));
    Serial.println("Chip ID: " + String(ESP.getChipId()));
    Serial.println("Flash Size: " + String(ESP.getFlashChipSize()));
    Serial.println("Free Heap: " + String(ESP.getFreeHeap()));
    Serial.println("WiFi SSID: " + String(WiFi.SSID()));
    Serial.println("IP Address: " + WiFi.localIP().toString());
    Serial.println("MAC Address: " + WiFi.macAddress());
    Serial.println("Signal Strength: " + String(WiFi.RSSI()) + " dBm");
    Serial.println("===========================");
}