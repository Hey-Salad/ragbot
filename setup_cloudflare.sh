#!/bin/bash

echo "☁️ Setting up Cloudflare Tunnel for RAG Bot..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Download and install cloudflared for ARM64 (Raspberry Pi)
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
    sudo dpkg -i cloudflared-linux-arm64.deb
    rm cloudflared-linux-arm64.deb
    
    echo "✅ cloudflared installed successfully"
else
    echo "✅ cloudflared already installed"
fi

echo ""
echo "🔐 Next steps:"
echo "1. Login to Cloudflare:"
echo "   cloudflared tunnel login"
echo ""
echo "2. Create a tunnel:"
echo "   cloudflared tunnel create ragbot"
echo ""
echo "3. Create tunnel configuration:"
echo "   nano ~/.cloudflared/config.yml"
echo ""
echo "4. Add this configuration:"
echo "   tunnel: <TUNNEL-ID>"
echo "   credentials-file: /home/pi/.cloudflared/<TUNNEL-ID>.json"
echo "   ingress:"
echo "     - hostname: ragbot.yourdomain.com"
echo "       service: http://localhost:8000"
echo "     - service: http_status:404"
echo ""
echo "5. Route DNS:"
echo "   cloudflared tunnel route dns ragbot ragbot.yourdomain.com"
echo ""
echo "6. Install tunnel as service:"
echo "   sudo cloudflared service install"
echo ""
echo "7. Start the tunnel:"
echo "   sudo systemctl start cloudflared"
echo "   sudo systemctl enable cloudflared"