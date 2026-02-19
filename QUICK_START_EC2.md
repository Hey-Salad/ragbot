# 🚀 Quick Start: Deploy Asterisk on EC2 in 15 Minutes

Simple guide to get your voice AI system running on AWS EC2.

---

## 📋 Prerequisites

- ✅ AWS Account
- ✅ Basic command line knowledge
- ✅ SSH key pair for EC2

---

## ⚡ Option 1: Automated Installation (Recommended)

### Step 1: Launch EC2 Instance

**AWS Console Method:**

1. Go to EC2 Dashboard
2. Click "Launch Instance"
3. Configure:
   - **Name**: `Asterisk-VoIP`
   - **AMI**: Ubuntu 22.04 LTS
   - **Instance Type**: `t3.small`
   - **Key Pair**: Select or create
   - **Security Group**: Create with these ports:
     - SSH (22) - TCP
     - SIP (5060) - UDP
     - RTP (10000-20000) - UDP
4. Click "Launch"

### Step 2: Connect to EC2

```bash
# Get public IP from AWS Console
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 3: Run Automated Installer

```bash
# Download the installer
wget https://raw.githubusercontent.com/your-repo/install_ec2_asterisk.sh

# Or copy from your local machine
scp -i your-key.pem install_ec2_asterisk.sh ubuntu@your-ec2-ip:~/

# Run the installer
sudo bash install_ec2_asterisk.sh
```

**Installation takes 10-15 minutes.**

### Step 4: Test

After installation completes, you'll see connection details:

```
SIP Server:   xx.xx.xx.xx
Username:     1000
Password:     <generated_during_install>
```

Test with a SIP client (Linphone, Zoiper, etc.)

---

## 🛠️ Option 2: Manual Installation

If you prefer manual control, follow the detailed guide:

```bash
# On your EC2 instance
nano /home/ubuntu/EC2_ASTERISK_SETUP.md
```

Or read it on your Raspberry Pi:
```bash
cat /home/admin/ragbot/EC2_ASTERISK_SETUP.md
```

---

## 🔗 Connect to Raspberry Pi

### Step 1: Update Pi Configuration

On your **Raspberry Pi**, edit `.env`:

```bash
cd /home/admin/ragbot
nano .env
```

Add:
```bash
# EC2 Asterisk Server
ASTERISK_SERVER_IP=your-ec2-public-ip
ASTERISK_AMI_HOST=your-ec2-public-ip
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=admin
ASTERISK_AMI_PASSWORD=<generated_during_install>
```

### Step 2: Create Voice Processing Endpoint

Add to `main.py` on your **Raspberry Pi**:

```python
from fastapi import FastAPI, UploadFile, File
from voice_agent_v2 import VoiceAgent
import tempfile
import os

app = FastAPI()

# Initialize voice agent
voice_agent = VoiceAgent(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY")
)

@app.post("/api/voice/process")
async def process_voice(audio: UploadFile = File(...)):
    """Process audio from EC2 Asterisk server"""
    try:
        # Save audio
        temp_file = tempfile.mktemp(suffix=".wav")
        with open(temp_file, "wb") as f:
            content = await audio.read()
            f.write(content)

        # Process with AI
        async def generate_ai_response(text):
            # Your RAG system here
            return f"I heard: {text}. How can I help you?"

        response_audio = await voice_agent.process_voice_call(
            temp_file,
            generate_ai_response
        )

        return {
            "status": "success",
            "response_audio_path": response_audio
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### Step 3: Update EC2 AGI Script

On **EC2**, edit the AGI bridge script:

```bash
sudo nano /var/lib/asterisk/agi-bin/voice_ai_bridge.py
```

Update the Raspberry Pi URL:
```python
RASPBERRY_PI_URL = "http://YOUR_PI_PUBLIC_IP:8000"
```

Make executable:
```bash
sudo chmod +x /var/lib/asterisk/agi-bin/voice_ai_bridge.py
```

### Step 4: Restart Services

**On EC2:**
```bash
sudo systemctl restart asterisk
```

**On Raspberry Pi:**
```bash
sudo systemctl restart ragbot.service
```

---

## 🧪 Testing the System

### Test 1: Basic SIP Connection

1. Download a SIP client (Linphone, Zoiper, MicroSIP)
2. Configure:
   - Server: your-ec2-ip
   - Username: 1000
   - Password: <generated_during_install>
3. Register
4. Call extension 1000

### Test 2: Echo Test

Call extension 9999 from your SIP client to test audio quality.

### Test 3: Voice AI Flow

1. Call extension 1000
2. Speak after beep: "What's the weather?"
3. Your voice → Asterisk → Raspberry Pi → Whisper (transcribe)
4. Transcription → RAG/GPT-OSS → Response text
5. Response → 11Labs (TTS) → Audio file
6. Audio → Asterisk → You hear AI response

---

## 📊 Monitoring

### Asterisk Console (EC2)

```bash
sudo asterisk -rvvv
```

Commands:
- `sip show peers` - Show registered SIP clients
- `core show channels` - Active calls
- `core show uptime` - Server uptime
- Type `exit` to quit

### Raspberry Pi Logs

```bash
tail -f /home/admin/ragbot/logs/ragbot.log
```

### EC2 CloudWatch (Optional)

AWS Console → CloudWatch → Metrics → EC2

Monitor:
- CPU utilization
- Network in/out
- Disk I/O

---

## 🔐 Security Checklist

- [x] Changed default SIP password
- [x] UFW firewall enabled
- [x] Fail2Ban installed
- [x] AMI only accessible from Pi IP
- [ ] Set up SSL/TLS for SIP (optional)
- [ ] Configure VPN between EC2 and Pi (optional)
- [ ] Enable AWS CloudWatch monitoring
- [ ] Set up automated backups

---

## 💰 Cost Breakdown

**Monthly Costs (Estimated):**

| Service | Cost |
|---------|------|
| EC2 t3.small (730 hrs) | $15.00 |
| EBS Storage (20GB) | $2.00 |
| Data Transfer (50GB) | $4.50 |
| **Total** | **~$21.50/month** |

**Cost Savings:**
- Use Reserved Instances: Save 40-60%
- t3a instances: Save 10%
- Stop instance when not in use: Save 100% compute

---

## 🆘 Troubleshooting

### Problem: SIP client won't register

**Solution:**
```bash
# Check Asterisk is running
sudo systemctl status asterisk

# Check SIP peers
sudo asterisk -rx "sip show peers"

# Check firewall
sudo ufw status

# Check security group allows port 5060 UDP
```

### Problem: No audio in calls

**Solution:**
```bash
# Check RTP ports open
sudo ufw status | grep 10000:20000

# Check NAT settings in sip.conf
sudo nano /etc/asterisk/sip.conf
# Verify externip is correct

# Reload SIP
sudo asterisk -rx "sip reload"
```

### Problem: AGI script fails

**Solution:**
```bash
# Check Pi is reachable from EC2
ping your-pi-ip

# Test AGI script manually
sudo /var/lib/asterisk/agi-bin/voice_ai_bridge.py

# Check logs
tail -f /var/log/asterisk/full
```

### Problem: High latency

**Solutions:**
1. Choose EC2 region closer to users
2. Upgrade to t3.medium or c5.large
3. Use EBS-optimized instance
4. Check network between EC2 and Pi

---

## 📈 Scaling Up

### Handle More Calls

**Vertical Scaling:**
```
t3.small  → t3.medium   (10-20 calls)
t3.medium → c5.large    (50+ calls)
c5.large  → c5.xlarge   (100+ calls)
```

**Horizontal Scaling:**
1. Launch multiple EC2 instances
2. Use AWS Elastic Load Balancer
3. DNS-based load balancing with Route 53

### Multi-Region Deployment

Deploy Asterisk in multiple regions:
- US East (N. Virginia) - `us-east-1`
- EU (Ireland) - `eu-west-1`
- Asia Pacific (Singapore) - `ap-southeast-1`

Use Route 53 geo-routing to send users to nearest region.

---

## 🎯 Next Steps

1. ✅ EC2 instance running Asterisk
2. ✅ Basic SIP working
3. ⏭️ Connect to Raspberry Pi
4. ⏭️ Test voice AI flow
5. ⏭️ Add SIP trunk for real phone numbers
6. ⏭️ Set up monitoring and alerts
7. ⏭️ Configure backups
8. ⏭️ Production hardening

---

## 📚 Resources

- **Full Setup Guide**: `EC2_ASTERISK_SETUP.md`
- **Asterisk Docs**: https://wiki.asterisk.org
- **AWS EC2**: https://docs.aws.amazon.com/ec2/
- **SIP Trunk Providers**:
  - Twilio: https://www.twilio.com/sip-trunking
  - Bandwidth: https://www.bandwidth.com/
  - Telnyx: https://telnyx.com/

---

**🎉 You're Ready to Go!**

Your scalable voice AI infrastructure is now running in the cloud!

**Questions?** Check `EC2_ASTERISK_SETUP.md` for detailed troubleshooting.
