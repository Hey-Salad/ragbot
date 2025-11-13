#!/bin/bash

echo "🔧 Installing RAG Bot as systemd service..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please run this script as the pi user, not root"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
SERVICE_FILE="ragbot.service"

# Update service file with correct paths
sed -i "s|/home/pi/ragbot|$CURRENT_DIR|g" $SERVICE_FILE

echo "📁 Updated service file with current directory: $CURRENT_DIR"

# Copy service file to systemd directory
sudo cp $SERVICE_FILE /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service
sudo systemctl enable ragbot.service

echo "✅ RAG Bot service installed successfully!"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ragbot"
echo "  Stop:    sudo systemctl stop ragbot"
echo "  Status:  sudo systemctl status ragbot"
echo "  Logs:    sudo journalctl -u ragbot -f"
echo ""
echo "The service will start automatically on boot."