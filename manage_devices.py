#!/usr/bin/env python3
"""
IoT DropSync - Device Management Utility
CLI tool for managing devices and system administration
"""

import argparse
import json
import requests
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class DeviceManager:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.auth_file = Path("app/device_auth.json")
    
    def load_auth_tokens(self) -> Dict[str, str]:
        """Load device authentication tokens"""
        if self.auth_file.exists():
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_auth_tokens(self, tokens: Dict[str, str]):
        """Save device authentication tokens"""
        with open(self.auth_file, 'w') as f:
            json.dump(tokens, f, indent=2)
    
    def list_devices(self, include_inactive: bool = False):
        """List all devices"""
        try:
            response = requests.get(
                f"{self.api_base}/admin/devices",
                params={"include_inactive": include_inactive}
            )
            
            if response.status_code == 200:
                data = response.json()
                devices = data.get("devices", [])
                
                if not devices:
                    print("No devices found.")
                    return
                
                print(f"\n📱 Devices ({len(devices)} total):")
                print("-" * 80)
                print(f"{'ID':<12} {'Name':<20} {'Type':<10} {'Status':<10} {'Last Seen':<20}")
                print("-" * 80)
                
                for device in devices:
                    last_seen = device.get('last_seen', 'Never')
                    if last_seen and last_seen != 'Never':
                        last_seen = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                        last_seen = last_seen.strftime('%Y-%m-%d %H:%M:%S')
                    
                    status_icon = "🟢" if device.get('is_online') else "🔴"
                    print(f"{device['device_id']:<12} {device['name']:<20} {device['device_type']:<10} {status_icon} {device['status']:<8} {last_seen}")
                
                print("-" * 80)
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def register_device(self, device_id: str, name: str = None, device_type: str = "esp8266"):
        """Register a new device"""
        try:
            data = {
                "device_id": device_id,
                "device_type": device_type
            }
            if name:
                data["name"] = name
            
            response = requests.post(
                f"{self.api_base}/admin/devices/register",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Device registered successfully!")
                print(f"   Device ID: {result['device_id']}")
                print(f"   Name: {result['name']}")
                print(f"   Type: {result['device_type']}")
                print(f"   Token: {result['token']}")
                
                # Update auth file
                tokens = self.load_auth_tokens()
                tokens[device_id] = result['token']
                self.save_auth_tokens(tokens)
                print(f"   Auth token saved to {self.auth_file}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def send_command(self, device_id: str, command: str, priority: int = 1):
        """Send a command to a device"""
        try:
            data = {
                "command": command,
                "priority": priority
            }
            
            response = requests.post(
                f"{self.api_base}/admin/devices/{device_id}/command",
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Command sent successfully!")
                print(f"   Command ID: {result['command_id']}")
                print(f"   Device: {result['device_id']}")
                print(f"   Command: {result['command']}")
                print(f"   Priority: {result['priority']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def get_device_messages(self, device_id: str, limit: int = 20):
        """Get messages from a device"""
        try:
            response = requests.get(
                f"{self.api_base}/admin/devices/{device_id}/messages",
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                if not messages:
                    print(f"No messages found for device {device_id}")
                    return
                
                print(f"\n💬 Messages from {device_id} ({len(messages)} total):")
                print("-" * 80)
                
                for msg in messages:
                    timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    
                    severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌"}.get(msg['severity'], "📝")
                    print(f"{severity_icon} [{timestamp_str}] {msg['type']}: {msg['content']}")
                
                print("-" * 80)
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
    
    def get_system_stats(self):
        """Get system statistics"""
        try:
            response = requests.get(f"{self.api_base}/admin/system/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                print("\n📊 System Statistics:")
                print("-" * 40)
                print(f"Total Devices: {stats['devices']['total']}")
                print(f"Active Devices: {stats['devices']['active']}")
                print(f"Online Devices: {stats['devices']['online']}")
                print(f"Pending Commands: {stats['commands']['pending']}")
                print(f"Total Messages: {stats['messages']['total']}")
                print("-" * 40)
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")

def main():
    parser = argparse.ArgumentParser(description="IoT DropSync Device Management")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List devices
    list_parser = subparsers.add_parser("list", help="List all devices")
    list_parser.add_argument("--include-inactive", action="store_true", help="Include inactive devices")
    
    # Register device
    register_parser = subparsers.add_parser("register", help="Register a new device")
    register_parser.add_argument("device_id", help="Device ID")
    register_parser.add_argument("--name", help="Device name")
    register_parser.add_argument("--type", default="esp8266", help="Device type")
    
    # Send command
    command_parser = subparsers.add_parser("send", help="Send command to device")
    command_parser.add_argument("device_id", help="Device ID")
    command_parser.add_argument("command", help="Command to send")
    command_parser.add_argument("--priority", type=int, default=1, help="Command priority (1-3)")
    
    # Get messages
    messages_parser = subparsers.add_parser("messages", help="Get device messages")
    messages_parser.add_argument("device_id", help="Device ID")
    messages_parser.add_argument("--limit", type=int, default=20, help="Number of messages to retrieve")
    
    # System stats
    subparsers.add_parser("stats", help="Get system statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DeviceManager(args.server)
    
    if args.command == "list":
        manager.list_devices(args.include_inactive)
    elif args.command == "register":
        manager.register_device(args.device_id, args.name, args.type)
    elif args.command == "send":
        manager.send_command(args.device_id, args.command, args.priority)
    elif args.command == "messages":
        manager.get_device_messages(args.device_id, args.limit)
    elif args.command == "stats":
        manager.get_system_stats()

if __name__ == "__main__":
    main()
