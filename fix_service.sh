#!/bin/bash

echo "🔧 Fixing RAG Bot service for current user..."

# Get current user and home directory
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
CURRENT_DIR=$(pwd)

echo "👤 Current user: $CURRENT_USER"
echo "🏠 Home directory: $CURRENT_HOME"
echo "📁 Current directory: $CURRENT_DIR"

# Create updated service file
cat > ragbot.service << EOF
[Unit]
Description=RAG Bot with GPT-OSS Integration
After=network.target
Wants=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python main.py
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ragbot

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$CURRENT_DIR/chroma_db $CURRENT_DIR/uploads $CURRENT_DIR/logs
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Updated service file for user: $CURRENT_USER"

# Stop the service if running
sudo systemctl stop ragbot 2>/dev/null || true

# Copy updated service file
sudo cp ragbot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable ragbot.service
sudo systemctl start ragbot.service

echo "🚀 Service restarted with correct user configuration"
echo ""
echo "Check status with: sudo systemctl status ragbot"