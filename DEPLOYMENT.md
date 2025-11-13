# 🚀 Deployment Guide for Raspberry Pi

This guide will help you deploy your RAG Bot on Raspberry Pi with systemd service and Cloudflare tunnel.

## 📋 Prerequisites

- Raspberry Pi with Raspbian OS
- Internet connection
- Cloudflare account with a domain

## 🔧 Step 1: Install as System Service

After cloning and setting up the bot on your Pi:

```bash
# Make the install script executable
chmod +x install_service.sh

# Install the systemd service
./install_service.sh
```

### Service Management Commands:
```bash
# Start the service
sudo systemctl start ragbot

# Stop the service
sudo systemctl stop ragbot

# Check status
sudo systemctl status ragbot

# View logs
sudo journalctl -u ragbot -f

# Restart service
sudo systemctl restart ragbot
```

## ☁️ Step 2: Setup Cloudflare Tunnel

### Install Cloudflared:
```bash
# Make setup script executable
chmod +x setup_cloudflare.sh

# Run the setup (installs cloudflared)
./setup_cloudflare.sh
```

### Configure Tunnel:

1. **Login to Cloudflare:**
   ```bash
   cloudflared tunnel login
   ```

2. **Create a tunnel:**
   ```bash
   cloudflared tunnel create ragbot
   ```
   Note the tunnel ID from the output.

3. **Create configuration file:**
   ```bash
   mkdir -p ~/.cloudflared
   nano ~/.cloudflared/config.yml
   ```

4. **Add this configuration:**
   ```yaml
   tunnel: YOUR-TUNNEL-ID-HERE
   credentials-file: /home/pi/.cloudflared/YOUR-TUNNEL-ID-HERE.json
   
   ingress:
     - hostname: ragbot.yourdomain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

5. **Route DNS:**
   ```bash
   cloudflared tunnel route dns ragbot ragbot.yourdomain.com
   ```

6. **Install tunnel as service:**
   ```bash
   sudo cloudflared service install
   sudo systemctl start cloudflared
   sudo systemctl enable cloudflared
   ```

## 🔍 Verification

### Check Services:
```bash
# Check RAG Bot service
sudo systemctl status ragbot

# Check Cloudflare tunnel
sudo systemctl status cloudflared

# Test local API
curl http://localhost:8000/health

# Test public endpoint
curl https://ragbot.yourdomain.com/health
```

### View Logs:
```bash
# RAG Bot logs
sudo journalctl -u ragbot -f

# Cloudflare tunnel logs
sudo journalctl -u cloudflared -f
```

## 🔒 Security Considerations

1. **Firewall**: The Cloudflare tunnel eliminates the need to open ports on your Pi
2. **HTTPS**: Cloudflare provides automatic SSL/TLS encryption
3. **Access Control**: Configure Cloudflare Access rules if needed
4. **Rate Limiting**: Set up rate limiting in Cloudflare dashboard

## 📱 WhatsApp Integration

Once your bot is publicly accessible via Cloudflare:

1. **Twilio Webhook URL**: `https://ragbot.yourdomain.com/whatsapp/webhook`
2. **Slack Events URL**: `https://ragbot.yourdomain.com/slack/events`

## 🔧 Troubleshooting

### Service Issues:
```bash
# If service fails to start
sudo systemctl status ragbot
sudo journalctl -u ragbot --no-pager

# Check file permissions
ls -la /home/pi/ragbot/
```

### Tunnel Issues:
```bash
# Check tunnel status
cloudflared tunnel info ragbot

# Test tunnel connectivity
cloudflared tunnel run ragbot
```

### Common Fixes:
- Ensure `.env` file has correct permissions: `chmod 600 .env`
- Check virtual environment path in service file
- Verify Cloudflare DNS settings
- Ensure port 8000 is not blocked locally

## 📊 Monitoring

### System Resources:
```bash
# Check CPU/Memory usage
htop

# Check disk space
df -h

# Check service resource usage
systemctl status ragbot
```

### Application Logs:
```bash
# Real-time logs
sudo journalctl -u ragbot -f

# Last 100 lines
sudo journalctl -u ragbot -n 100
```