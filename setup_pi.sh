#!/bin/bash

# IoT DropSync - Raspberry Pi 5 Auto Setup Script
# This script automates the setup process for the IoT DropSync hub server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="dropsync"
VENV_DIR="venv"
SERVICE_NAME="dropsync"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

check_pi() {
    if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
        print_warning "This script is designed for Raspberry Pi, but continuing anyway..."
    fi
}

update_system() {
    print_status "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    print_success "System updated"
}

install_dependencies() {
    print_status "Installing system dependencies..."
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        build-essential \
        libssl-dev \
        libffi-dev \
        sqlite3
    print_success "Dependencies installed"
}

setup_python_environment() {
    print_status "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv $VENV_DIR
    fi
    
    source $VENV_DIR/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python packages installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

create_config_files() {
    print_status "Creating configuration files..."
    
    # Create device auth file
    if [ ! -f "app/device_auth.json" ]; then
        cat > app/device_auth.json << 'EOF'
{
  "esp001": "secure-token-esp001-xyz123",
  "esp002": "secure-token-esp002-abc456",
  "esp003": "secure-token-esp003-def789"
}
EOF
        print_success "Device auth file created"
    else
        print_warning "Device auth file already exists"
    fi
    
    # Create environment file
    if [ ! -f ".env" ]; then
        cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
EOF
        print_success "Environment file created"
    else
        print_warning "Environment file already exists"
    fi
}

create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p app/uploads
    mkdir -p app/logs
    mkdir -p app/static
    
    print_success "Directories created"
}

setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    WORKING_DIR="$(pwd)"
    USER="$(whoami)"
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=IoT DropSync Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORKING_DIR
Environment=PATH=$WORKING_DIR/$VENV_DIR/bin
ExecStart=$WORKING_DIR/$VENV_DIR/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    print_success "Systemd service configured"
}

setup_firewall() {
    print_status "Configuring firewall..."
    
    # Check if ufw is installed
    if command -v ufw &> /dev/null; then
        sudo ufw allow 8000/tcp
        print_success "Firewall configured to allow port 8000"
    else
        print_warning "UFW firewall not found, skipping firewall configuration"
    fi
}

get_network_info() {
    print_status "Getting network information..."
    
    IP_ADDRESS=$(ip route get 1 | awk '{print $NF;exit}')
    
    echo ""
    echo "=================================="
    echo "   NETWORK CONFIGURATION"
    echo "=================================="
    echo "Pi IP Address: $IP_ADDRESS"
    echo "Server will be available at:"
    echo "  - Dashboard: http://$IP_ADDRESS:8000/dashboard"
    echo "  - API Docs:  http://$IP_ADDRESS:8000/api/v1/docs"
    echo "  - Health:    http://$IP_ADDRESS:8000/health"
    echo ""
    echo "ESP8266 Configuration:"
    echo "  const char* server = \"http://$IP_ADDRESS:8000\";"
    echo "=================================="
    echo ""
}

test_installation() {
    print_status "Testing installation..."
    
    source $VENV_DIR/bin/activate
    
    # Test Python imports
    if python3 -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null; then
        print_success "Python dependencies OK"
    else
        print_error "Python dependencies test failed"
        exit 1
    fi
    
    # Test database creation
    if python3 -c "from app.database import init_database; init_database()" 2>/dev/null; then
        print_success "Database initialization OK"
    else
        print_error "Database initialization failed"
        exit 1
    fi
}

start_service() {
    print_status "Starting IoT DropSync service..."
    
    sudo systemctl start $SERVICE_NAME
    
    # Wait a moment for service to start
    sleep 3
    
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Service started successfully"
    else
        print_error "Service failed to start"
        echo "Check logs with: sudo journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
}

main() {
    echo "========================================"
    echo "   IoT DropSync - Raspberry Pi Setup"
    echo "========================================"
    echo ""
    
    check_root
    check_pi
    
    # Check if we're in the right directory
    if [ ! -f "requirements.txt" ] || [ ! -d "app" ]; then
        print_error "Please run this script from the dropsync project directory"
        exit 1
    fi
    
    update_system
    install_dependencies
    setup_python_environment
    create_config_files
    create_directories
    setup_systemd_service
    setup_firewall
    test_installation
    start_service
    get_network_info
    
    echo ""
    print_success "🎉 IoT DropSync setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure your ESP8266 with the IP address shown above"
    echo "2. Upload the Arduino code to your ESP8266"
    echo "3. Open the dashboard in your browser"
    echo ""
    echo "Useful commands:"
    echo "  sudo systemctl status $SERVICE_NAME    # Check service status"
    echo "  sudo systemctl restart $SERVICE_NAME   # Restart service"
    echo "  sudo journalctl -u $SERVICE_NAME -f    # View logs"
    echo ""
}

# Run main function
main "$@"
