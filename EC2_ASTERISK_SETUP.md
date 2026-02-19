# 🌐 Asterisk on AWS EC2 - Complete Setup Guide

Deploy production-ready Asterisk SIP server on AWS EC2 integrated with your Raspberry Pi AI backend.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                             │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │   SIP Clients   │
        │ (Phones/Softph) │
        └────────┬────────┘
                 │ SIP/RTP
                 │
┌────────────────▼────────────────────────────────────────────┐
│              AWS EC2 (Asterisk Server)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Asterisk PBX                                       │   │
│  │  • SIP Server (Port 5060)                          │   │
│  │  • RTP Media (Ports 10000-20000)                   │   │
│  │  • AGI Interface                                    │   │
│  │  • Recording Storage                                │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │ HTTP/WebSocket                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  API Bridge (Flask/FastAPI)                         │   │
│  │  • Asterisk Manager Interface (AMI)                 │   │
│  │  • AGI Scripts                                       │   │
│  └─────────────────┬───────────────────────────────────┘   │
└────────────────────┼───────────────────────────────────────┘
                     │ HTTPS/WebSocket
                     │
┌────────────────────▼───────────────────────────────────────┐
│         Raspberry Pi 5 (AI Processing)                     │
│  ┌──────────────────────────────────────────────────┐     │
│  │  Voice Agent                                     │     │
│  │  • OpenAI Whisper (STT)                         │     │
│  │  • 11Labs (TTS)                                  │     │
│  │  • RAG System (ChromaDB)                        │     │
│  │  • GPT-OSS (Hugging Face)                       │     │
│  └──────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────┘
```

---

## 📋 Part 1: Launch EC2 Instance

### 1.1 EC2 Instance Specifications

**Recommended Configuration:**
- **Instance Type**: `t3.small` (2 vCPU, 2GB RAM) for testing
- **Production**: `t3.medium` or `c5.large` for 50+ concurrent calls
- **AMI**: Ubuntu 22.04 LTS (HVM)
- **Storage**: 20GB gp3 SSD
- **Region**: Choose closest to your users

### 1.2 Launch Instance

```bash
# Using AWS CLI (if you have it configured)
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \  # Ubuntu 22.04 (check your region)
  --instance-type t3.small \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxxx \
  --subnet-id subnet-xxxxxxxxx \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=Asterisk-VoIP}]'
```

Or use the AWS Console:
1. EC2 Dashboard → Launch Instance
2. Name: `Asterisk-VoIP-Server`
3. Choose Ubuntu 22.04 LTS
4. Instance type: t3.small
5. Key pair: Create or select existing
6. Network: Default VPC
7. Launch

### 1.3 Configure Security Group

**Required Ports:**

| Port Range    | Protocol | Purpose              |
|---------------|----------|----------------------|
| 22            | TCP      | SSH                  |
| 5060          | UDP      | SIP Signaling        |
| 5061          | TCP      | SIP TLS (optional)   |
| 10000-20000   | UDP      | RTP Media            |
| 8088          | TCP      | Asterisk HTTP (AMI)  |
| 8089          | TCP      | Asterisk HTTPS       |

**Create Security Group:**

```bash
# Create security group
aws ec2 create-security-group \
  --group-name asterisk-sg \
  --description "Asterisk VoIP Server"

# Add rules
aws ec2 authorize-security-group-ingress \
  --group-name asterisk-sg \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name asterisk-sg \
  --protocol udp --port 5060 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name asterisk-sg \
  --protocol udp --port 10000-20000 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name asterisk-sg \
  --protocol tcp --port 8088 --cidr YOUR_PI_IP/32
```

---

## 📦 Part 2: Install Asterisk on EC2

### 2.1 Connect to EC2

```bash
# Get your instance public IP from AWS Console
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
```

### 2.2 Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential wget libssl-dev libncurses5-dev \
  libnewt-dev libxml2-dev linux-headers-$(uname -r) libsqlite3-dev \
  uuid-dev git subversion
```

### 2.3 Install Asterisk

```bash
cd /usr/src

# Download Asterisk (latest LTS version)
sudo wget https://downloads.asterisk.org/pub/telephony/asterisk/asterisk-20-current.tar.gz
sudo tar -xvzf asterisk-20-current.tar.gz
cd asterisk-20.*

# Install prerequisites
sudo contrib/scripts/install_prereq install

# Configure
sudo ./configure --with-jansson-bundled

# Select modules (optional - for custom build)
sudo make menuselect
# Navigate: Applications → Select 'app_macro' if needed
# Save and exit

# Compile (this takes 10-20 minutes)
sudo make -j$(nproc)

# Install
sudo make install
sudo make samples
sudo make config
sudo ldconfig

# Start Asterisk
sudo systemctl enable asterisk
sudo systemctl start asterisk

# Verify
sudo asterisk -rx "core show version"
```

### 2.4 Install Additional Tools

```bash
# FFmpeg for audio conversion
sudo apt-get install -y ffmpeg

# Python for AGI scripts
sudo apt-get install -y python3-pip python3-dev
pip3 install asterisk-ami requests

# Audio codecs
sudo apt-get install -y asterisk-core-sounds-en-wav \
  asterisk-core-sounds-en-gsm \
  asterisk-moh-opsound-wav
```

---

## 🔧 Part 3: Configure Asterisk

### 3.1 Basic Configuration

**Edit `/etc/asterisk/sip.conf`:**

```bash
sudo nano /etc/asterisk/sip.conf
```

```ini
[general]
context=default
allowguest=no
udpbindaddr=0.0.0.0:5060
tcpenable=yes
tcpbindaddr=0.0.0.0:5060

; NAT settings for AWS
nat=force_rport,comedia
externip=YOUR_EC2_PUBLIC_IP
localnet=172.31.0.0/16  ; AWS VPC CIDR

; Security
alwaysauthreject=yes
allowoverlap=no
dtmfmode=rfc2833

; Codecs
disallow=all
allow=ulaw
allow=alaw
allow=gsm

; RTP settings
rtpstart=10000
rtpend=20000

; --- SIP Peers/Trunks ---

; Example SIP trunk (your provider)
[trunk-provider]
type=peer
host=sip.yourprovider.com
username=YOUR_USERNAME
secret=YOUR_PASSWORD
fromuser=YOUR_USERNAME
fromdomain=sip.yourprovider.com
context=from-trunk
insecure=port,invite
canreinvite=no

; Internal extension for testing
[1000]
type=friend
secret=secure_password_here
host=dynamic
context=internal
```

**Get your EC2 public IP:**
```bash
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

### 3.2 Dialplan Configuration

**Edit `/etc/asterisk/extensions.conf`:**

```bash
sudo nano /etc/asterisk/extensions.conf
```

```ini
[general]
static=yes
writeprotect=no

; ==========================================
; Voice AI Agent Context
; ==========================================
[voice-ai-agent]

; Main voice AI extension
exten => 1000,1,NoOp(Voice AI Agent Starting)
    same => n,Answer()
    same => n,Wait(0.5)
    same => n,Playback(beep)

    ; Record user audio
    same => n,Set(RECORDING_FILE=/var/spool/asterisk/recording/${UNIQUEID}.wav)
    same => n,Record(${RECORDING_FILE},3,60,q)

    ; Send to Raspberry Pi for AI processing
    same => n,AGI(voice_ai_bridge.py,${RECORDING_FILE})

    ; Play AI response
    same => n,GotoIf($["${AI_RESPONSE_FILE}" = ""]?error)
    same => n,Playback(${AI_RESPONSE_FILE})

    ; Loop for conversation
    same => n,Goto(1000,1)

    ; Error handling
    same => n(error),Playback(tt-weasels)  ; Error sound
    same => n,Hangup()

; ==========================================
; Incoming calls from trunk
; ==========================================
[from-trunk]
exten => _X.,1,NoOp(Incoming call from trunk)
    same => n,Goto(voice-ai-agent,1000,1)

; ==========================================
; Internal testing context
; ==========================================
[internal]
exten => 1000,1,Goto(voice-ai-agent,1000,1)

; Echo test
exten => 9999,1,Answer()
    same => n,Playback(demo-echotest)
    same => n,Echo()
    same => n,Hangup()
```

### 3.3 Enable Asterisk Manager Interface (AMI)

**Edit `/etc/asterisk/manager.conf`:**

```bash
sudo nano /etc/asterisk/manager.conf
```

```ini
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[admin]
secret = YOUR_STRONG_PASSWORD_HERE
read = all
write = all
```

### 3.4 Enable HTTP Server (for API)

**Edit `/etc/asterisk/http.conf`:**

```bash
sudo nano /etc/asterisk/http.conf
```

```ini
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
enablestatic=yes
```

### 3.5 Reload Asterisk

```bash
sudo asterisk -rx "core reload"
sudo asterisk -rx "sip reload"
sudo asterisk -rx "dialplan reload"

# Check status
sudo asterisk -rx "sip show peers"
sudo asterisk -rx "core show channels"
```

---

## 🔗 Part 4: Bridge to Raspberry Pi

### 4.1 Create AGI Bridge Script on EC2

```bash
sudo nano /var/lib/asterisk/agi-bin/voice_ai_bridge.py
```

```python
#!/usr/bin/env python3
"""
AGI Bridge: Connects Asterisk (EC2) to Voice AI Agent (Raspberry Pi)
"""
import sys
import requests
import os
import time

# Configuration
RASPBERRY_PI_URL = "http://YOUR_PI_IP:8000"  # Update with your Pi's IP
API_KEY = "your_api_key_here"

def agi_response(message):
    """Send response to Asterisk AGI"""
    print(message)
    sys.stdout.flush()

def main():
    # Read AGI environment
    env = {}
    while True:
        line = sys.stdin.readline().strip()
        if line == '':
            break
        key, value = line.split(':', 1)
        env[key.strip()] = value.strip()

    # Get recording file from argument
    if len(sys.argv) < 2:
        agi_response("VERBOSE \"No recording file provided\" 1")
        agi_response("SET VARIABLE AI_RESPONSE_FILE \"\"")
        sys.exit(1)

    recording_file = sys.argv[1]

    # Wait for file to be ready
    time.sleep(1)

    try:
        # Send audio to Raspberry Pi
        with open(recording_file, 'rb') as audio_file:
            files = {'audio': audio_file}
            headers = {'Authorization': f'Bearer {API_KEY}'}

            response = requests.post(
                f"{RASPBERRY_PI_URL}/api/voice/process",
                files=files,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Get response audio file path
            response_audio = result.get('response_audio_path', '')

            if response_audio:
                agi_response(f"SET VARIABLE AI_RESPONSE_FILE \"{response_audio}\"")
                agi_response("VERBOSE \"AI processing successful\" 1")
            else:
                agi_response("SET VARIABLE AI_RESPONSE_FILE \"\"")
                agi_response("VERBOSE \"No response audio received\" 1")

    except Exception as e:
        agi_response(f"VERBOSE \"Error: {str(e)}\" 1")
        agi_response("SET VARIABLE AI_RESPONSE_FILE \"\"")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

```bash
# Make executable
sudo chmod +x /var/lib/asterisk/agi-bin/voice_ai_bridge.py

# Test
sudo /var/lib/asterisk/agi-bin/voice_ai_bridge.py
```

### 4.2 Create API Endpoint on Raspberry Pi

Add to your `/home/admin/ragbot/main.py`:

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from voice_agent_v2 import VoiceAgent
import tempfile
import os

app = FastAPI()
voice_agent = VoiceAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
)

@app.post("/api/voice/process")
async def process_voice(audio: UploadFile = File(...)):
    """Process voice audio and return AI response"""
    try:
        # Save uploaded audio
        temp_input = tempfile.mktemp(suffix=".wav")
        with open(temp_input, "wb") as f:
            f.write(await audio.read())

        # Define AI response generator
        async def generate_response(user_text):
            # Use your RAG system here
            from user_rag_system import UserRAGSystem
            rag = UserRAGSystem()
            response = rag.query_with_context("voice_user", user_text)
            return response

        # Process with voice agent
        response_audio = await voice_agent.process_voice_call(
            temp_input,
            generate_response
        )

        return {
            "status": "success",
            "response_audio_path": response_audio,
            "transcription": "..." # Optional: include transcription
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🔐 Part 5: Security & Firewall

### 5.1 UFW Firewall (Ubuntu)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow SIP
sudo ufw allow 5060/udp

# Allow RTP range
sudo ufw allow 10000:20000/udp

# Allow AMI (only from Pi IP)
sudo ufw allow from YOUR_PI_IP to any port 5038 proto tcp

# Check status
sudo ufw status
```

### 5.2 Fail2Ban (Prevent attacks)

```bash
sudo apt-get install -y fail2ban

# Configure for Asterisk
sudo nano /etc/fail2ban/jail.local
```

```ini
[asterisk]
enabled = true
port = 5060
protocol = udp
filter = asterisk
logpath = /var/log/asterisk/full
maxretry = 5
bantime = 3600
```

```bash
sudo systemctl restart fail2ban
```

---

## 🧪 Part 6: Testing

### 6.1 Test SIP Registration

From a SIP client (like Linphone, Zoiper):
```
Server: your-ec2-public-ip
Username: 1000
Password: secure_password_here
```

### 6.2 Test Voice AI

1. Call extension 1000
2. Speak after beep
3. Wait for AI response

### 6.3 Monitor Logs

```bash
# Asterisk console
sudo asterisk -rvvv

# Real-time logs
tail -f /var/log/asterisk/full

# Check SIP
sudo asterisk -rx "sip show peers"
```

---

## 📊 Part 7: Monitoring & Maintenance

### 7.1 CloudWatch Monitoring (AWS)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure metrics
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### 7.2 Asterisk Statistics

```bash
# Create monitoring script
sudo nano /usr/local/bin/asterisk_stats.sh
```

```bash
#!/bin/bash
echo "=== Asterisk Status ==="
asterisk -rx "core show uptime"
asterisk -rx "core show channels"
asterisk -rx "sip show peers"
asterisk -rx "core show calls"
```

```bash
sudo chmod +x /usr/local/bin/asterisk_stats.sh

# Add to cron
crontab -e
*/5 * * * * /usr/local/bin/asterisk_stats.sh >> /var/log/asterisk_stats.log
```

---

## 💰 Part 8: Cost Optimization

### Monthly Costs (Estimated):

- **EC2 t3.small**: ~$15/month (730 hours)
- **Data Transfer**: ~$5/month (50GB out)
- **Elastic IP**: Free (if attached)
- **EBS Storage**: ~$2/month (20GB)

**Total**: ~$22/month for VoIP infrastructure

### Cost Saving Tips:

1. Use Reserved Instances (save 40-60%)
2. Enable Auto Scaling for peak times
3. Use spot instances for testing
4. Compress audio files
5. Use regional data transfer

---

## 🔄 Part 9: Backup & Disaster Recovery

```bash
# Backup script
sudo nano /usr/local/bin/backup_asterisk.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/asterisk_backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configs
tar -czf $BACKUP_DIR/asterisk_config_$DATE.tar.gz /etc/asterisk/

# Backup recordings
tar -czf $BACKUP_DIR/recordings_$DATE.tar.gz /var/spool/asterisk/recording/

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/asterisk_config_$DATE.tar.gz s3://your-bucket/

echo "Backup completed: $DATE"
```

---

## 📞 Quick Reference Commands

```bash
# Restart Asterisk
sudo systemctl restart asterisk

# Reload config
sudo asterisk -rx "core reload"

# Check SIP peers
sudo asterisk -rx "sip show peers"

# Check active calls
sudo asterisk -rx "core show channels"

# Console access
sudo asterisk -rvvv

# Exit console
Type: exit

# Check logs
tail -f /var/log/asterisk/full
```

---

## 🎯 Next Steps

1. ✅ Launch EC2 instance
2. ✅ Install Asterisk
3. ✅ Configure SIP
4. ✅ Create AGI bridge
5. ✅ Test with Raspberry Pi
6. ✅ Set up monitoring
7. ✅ Configure backups

---

**🎉 You now have enterprise-grade voice infrastructure!**

Cost: ~$22/month | Scale: 50+ concurrent calls | Quality: Excellent
