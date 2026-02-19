# 🚀 Complete Integration Guide

**Services Integrated:**
- ✅ Infobip (WhatsApp + SMS)
- ✅ Slack (Team collaboration)
- ✅ OpenAI Whisper (Speech-to-Text)
- ✅ 11Labs (Text-to-Speech)
- ✅ Asterisk SIP (Voice calls)
- ✅ RAG System (Document Q&A)
- ✅ GPT-OSS via Hugging Face

---

## 📋 Prerequisites

### 1. API Keys Required

**Infobip Account:**
1. Sign up at https://www.infobip.com
2. Get API key from portal
3. Configure WhatsApp sender number
4. Note your base URL (usually https://api.infobip.com)

**Slack App:**
1. Create app at https://api.slack.com/apps
2. Add bot token scopes: `app_mentions:read`, `chat:write`, `files:read`
3. Enable events: `app_mention`, `message.channels`
4. Install to workspace

**OpenAI:**
1. Get API key from https://platform.openai.com/api-keys
2. Used for Whisper speech-to-text

**11Labs:**
1. Sign up at https://elevenlabs.io
2. Get API key from settings
3. Choose voice ID (default: Rachel)

**Hugging Face:**
1. Get token from https://huggingface.co/settings/tokens
2. Used for GPT-OSS model access

---

## 🛠️ Installation

### Step 1: Install Dependencies

```bash
cd /home/admin/ragbot

# Install Python packages
pip install -r requirements.txt.new

# Install system dependencies
sudo apt-get update
sudo apt-get install -y ffmpeg asterisk

# Install Playwright browsers (for web scraping)
playwright install chromium
```

### Step 2: Configure Environment

```bash
# Copy new env template
cp .env.example.new .env

# Edit with your credentials
nano .env
```

Fill in:
```bash
# Infobip
INFOBIP_API_KEY=your_key_here
INFOBIP_WHATSAPP_NUMBER=447123456789

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...

# OpenAI
OPENAI_API_KEY=sk-...

# 11Labs
ELEVENLABS_API_KEY=...

# Hugging Face
HUGGINGFACE_API_TOKEN=hf_...
```

### Step 3: Test Each Integration

**Test Infobip:**
```bash
python infobip_client.py
```

**Test Voice Agent:**
```bash
python voice_agent_v2.py
```

**Test WhatsApp Bot:**
```bash
python whatsapp_bot_infobip.py
```

---

## 🔧 Asterisk SIP Configuration

### 1. Configure Asterisk Extensions

Edit `/etc/asterisk/extensions.conf`:

```ini
[voice-agent]
; Incoming call handler
exten => 1000,1,Answer()
    same => n,Wait(1)
    same => n,Playback(welcome)
    same => n,Set(UNIQUEID=${UNIQUEID})
    same => n,Record(/var/spool/asterisk/recording/${UNIQUEID}.wav,3,60,q)
    same => n,AGI(voice_agent.py)
    same => n,Playback(${response_audio})
    same => n,Goto(1000,1)
    same => n,Hangup()

; Alternative: Direct AI response
exten => 2000,1,Answer()
    same => n,AGI(voice_agent_realtime.py)
    same => n,Hangup()
```

### 2. Configure SIP Trunk

Edit `/etc/asterisk/sip.conf`:

```ini
[general]
context=default
allowguest=no
udpbindaddr=0.0.0.0
tcpenable=yes
tcpbindaddr=0.0.0.0

[your-sip-provider]
type=friend
host=sip.yourprovider.com
username=your_username
secret=your_password
context=voice-agent
dtmfmode=rfc2833
canreinvite=no
```

### 3. Create AGI Script

```bash
cd /var/lib/asterisk/agi-bin
sudo nano voice_agent.py
```

Paste the AGI script from voice_agent_v2.py (it auto-generates)

```bash
sudo chmod +x /var/lib/asterisk/agi-bin/voice_agent.py
```

### 4. Restart Asterisk

```bash
sudo systemctl restart asterisk
sudo asterisk -rx "core reload"
```

---

## 🌐 Webhook Configuration

### Infobip WhatsApp Webhook

In Infobip portal:
1. Go to Channels → WhatsApp
2. Set webhook URL: `https://your-domain.com/whatsapp/webhook`
3. Enable: Message Received, Delivery Report

### Slack Events

In Slack app settings:
1. Enable Event Subscriptions
2. Request URL: `https://your-domain.com/slack/events`
3. Subscribe to: `app_mention`, `message.channels`

---

## 🚀 Running the Service

### Development Mode

```bash
cd /home/admin/ragbot
python main.py
```

### Production Mode (systemd)

```bash
# Use existing service
sudo systemctl restart ragbot.service
sudo systemctl status ragbot.service

# View logs
journalctl -u ragbot.service -f
```

---

## 📞 Testing Voice Calls

### 1. Call Your SIP Extension

Dial extension `1000` from any SIP client

### 2. Test Flow

1. System answers: "Welcome to HeySalad AI"
2. You speak: "What's on the menu today?"
3. System records your audio
4. Whisper transcribes it
5. RAG system processes query
6. 11Labs synthesizes response
7. System plays back audio

### 3. Check Logs

```bash
tail -f /var/log/asterisk/full
tail -f logs/ragbot.log
```

---

## 📱 Testing WhatsApp (Infobip)

### Send Test Message

```bash
curl -X POST "https://api.infobip.com/whatsapp/1/message/text" \
  -H "Authorization: App YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "YOUR_SENDER_NUMBER",
    "to": "447123456789",
    "content": {
      "text": "Hello from HeySalad!"
    }
  }'
```

### Test Webhook

Send a WhatsApp message to your number, check logs:

```bash
tail -f logs/ragbot.log | grep "whatsapp"
```

---

## 💬 Testing Slack

1. Mention your bot in a channel: `@ragbot hello`
2. Upload a document and mention bot
3. Check bot responds in thread

---

## 🔍 Troubleshooting

### Infobip Connection Issues

```bash
# Test API connectivity
curl -H "Authorization: App YOUR_KEY" \
  https://api.infobip.com/whatsapp/1/senders

# Check webhook is reachable
curl https://your-domain.com/health
```

### Asterisk Not Recording

```bash
# Check permissions
sudo chown -R asterisk:asterisk /var/spool/asterisk/recording
sudo chmod 755 /var/spool/asterisk/recording

# Test recording manually
asterisk -rx "core show channels"
```

### Voice Quality Issues

```bash
# Install proper audio codecs
sudo apt-get install asterisk-core-sounds-en-wav
sudo apt-get install asterisk-moh-opsound-wav

# Check FFmpeg installed
ffmpeg -version
```

### 11Labs Quota Exceeded

- Check usage at https://elevenlabs.io/usage
- Upgrade plan or use alternative TTS
- Implement caching for common responses

---

## 📊 Monitoring & Logs

```bash
# Application logs
tail -f logs/ragbot.log

# Asterisk logs
tail -f /var/log/asterisk/full

# System logs
journalctl -u ragbot.service -f

# Check service status
curl http://localhost:8000/health
```

---

## 🔐 Security Best Practices

1. **Environment Variables**: Never commit `.env` to git
2. **Webhook Validation**: Validate Infobip webhook signatures
3. **API Keys**: Rotate regularly
4. **Firewall**: Restrict Asterisk SIP ports
5. **HTTPS**: Always use SSL for webhooks

---

## 📈 Scalability

### Current Architecture (Single Pi)
- Handles: 10-50 concurrent users
- Voice calls: 2-3 simultaneous
- WhatsApp: 100+ messages/min

### Scale Up Options

**Option 1: Add More Raspberry Pis**
- Use Nghttp2/HAProxy for load balancing
- Share ChromaDB via network storage
- Distribute by channel (one Pi per service)

**Option 2: Cloud Hybrid**
- Keep bots on Pi
- Move AI processing to cloud
- Use Redis for message queue

**Option 3: Full Cloud Migration**
- AWS ECS or Google Cloud Run
- Managed databases
- Auto-scaling enabled

---

## 🎯 Next Steps

1. ✅ Get all API keys
2. ✅ Configure `.env` file
3. ✅ Install dependencies
4. ✅ Test each integration individually
5. ✅ Configure Asterisk SIP
6. ✅ Set up webhooks
7. ✅ Run production service
8. ✅ Monitor and optimize

---

## 📞 Support

- GitHub Issues: [Your repo]
- Email: peter@saladhr.com
- Slack: [Your workspace]

---

**Built with ❤️ for HeySalad**
*Powered by Infobip, OpenAI, 11Labs, and Asterisk*
