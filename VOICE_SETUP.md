# 📞 Voice Agent Setup Guide

Your RAG Bot now supports **three communication channels**:
1. 📞 **Voice Calls** - Talk to the bot
2. 💬 **SMS/Text** - Text the bot  
3. 📱 **WhatsApp** - Message on WhatsApp

All channels use the same RAG knowledge base!

## 🎯 Architecture

```
┌─────────────┐
│   Caller    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Twilio Phone Number         │
└──────┬──────────────────────────────┘
       │
       ├──► Voice Call  → /voice/webhook  → Voice Agent
       ├──► SMS         → /sms/webhook    → Text Agent  
       └──► WhatsApp    → /whatsapp/webhook → WhatsApp Agent
                                │
                                ▼
                         ┌──────────────┐
                         │  RAG System  │
                         │  (ChromaDB)  │
                         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   GPT-OSS    │
                         └──────────────┘
```

## 🔧 Twilio Configuration

### Step 1: Get a Twilio Phone Number

1. Go to https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Buy a phone number (or use existing)
3. Note your phone number (e.g., +1234567890)

### Step 2: Configure Voice Webhook

1. Click on your phone number
2. Under **Voice Configuration**:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://ragbot.heysalad.app/voice/webhook`
   - **HTTP**: POST
3. Click **Save**

### Step 3: Configure SMS Webhook

1. Same phone number settings
2. Under **Messaging Configuration**:
   - **A MESSAGE COMES IN**: Webhook
   - **URL**: `https://ragbot.heysalad.app/sms/webhook`
   - **HTTP**: POST
3. Click **Save**

### Step 4: WhatsApp Already Configured ✅

Your WhatsApp webhook is already set to:
`https://ragbot.heysalad.app/whatsapp/webhook`

## 📱 How to Use

### Voice Calls:
1. **Call** your Twilio phone number
2. **Listen** to the greeting
3. **Speak** your question after the beep
4. **Hear** the AI response
5. **Continue** or hang up

Example conversation:
```
Bot: "Hello! Welcome to RAG Bot. Please ask your question."
You: "What is machine learning?"
Bot: "Machine learning is a method of data analysis..."
Bot: "Would you like to ask another question?"
You: "Yes"
Bot: "Great! Please ask your next question."
```

### SMS/Text:
1. **Text** your Twilio phone number
2. Send: `hello`, `help`, `stats`, or any question
3. **Receive** text response

Example:
```
You: "What is AI?"
Bot: "🤖 RAG Bot Response: Artificial Intelligence is..."
```

### WhatsApp:
1. **Message** your WhatsApp-enabled number
2. Use commands: `research <topic>`, `scrape <url>`
3. **Get** intelligent responses

## 🧪 Testing

### Test Voice:
```bash
# Call your Twilio number from your phone
# Or use Twilio Console to make a test call
```

### Test SMS:
```bash
# Send SMS to your Twilio number
# Or test via API:
curl -X POST "https://ragbot.heysalad.app/sms/webhook" \
  -d "From=+1234567890" \
  -d "Body=What is AI?"
```

### Test WhatsApp:
```
# Already working! ✅
Send: "research quantum computing"
```

## 🎙️ Voice Features

### Supported Commands (Voice):
- Ask any question from knowledge base
- Natural conversation flow
- Multi-turn conversations
- Polite greetings and farewells

### Voice Characteristics:
- **Voice**: Amazon Polly (Joanna)
- **Language**: English (US)
- **Speech Recognition**: Twilio's built-in
- **Response Time**: ~2-3 seconds

## 📊 Monitoring

### Check Logs:
```bash
# RAG Bot logs
sudo journalctl -u ragbot -f

# Look for:
# - "Voice call from +1234567890"
# - "Speech from CallSid: ..."
# - "SMS from +1234567890"
```

### Twilio Console:
- Monitor calls: https://console.twilio.com/us1/monitor/logs/calls
- Monitor SMS: https://console.twilio.com/us1/monitor/logs/sms
- Monitor WhatsApp: https://console.twilio.com/us1/monitor/logs/whatsapp

## 🚀 Advanced: OpenAI Realtime API

For more natural conversations with streaming audio, you can upgrade to OpenAI Realtime API:

1. Get OpenAI API key
2. Enable Realtime API access
3. Update voice_agent.py to use VoiceAgentRealtime
4. Configure WebSocket endpoint

This provides:
- Lower latency
- More natural conversations
- Interruption handling
- Better voice quality

## 💰 Costs

### Twilio Pricing (Approximate):
- **Voice**: $0.0085/min (incoming)
- **SMS**: $0.0075/message (incoming)
- **WhatsApp**: $0.005/message (incoming)

### Your Costs:
- **GPT-OSS**: Via Hugging Face (your token)
- **Hosting**: Raspberry Pi (free!)
- **Tunnel**: Cloudflare (free!)

## 🔒 Security

- All traffic encrypted via HTTPS
- Twilio validates webhook signatures
- No sensitive data stored
- Cloudflare DDoS protection

## 🎯 Use Cases

1. **Customer Support**: Answer FAQs via voice/text
2. **Information Hotline**: Call for information
3. **Personal Assistant**: Multi-modal access
4. **Knowledge Base**: Voice-enabled search
5. **Accessibility**: Voice option for visually impaired

## 📝 Next Steps

1. ✅ Configure Twilio webhooks
2. ✅ Test voice calls
3. ✅ Test SMS
4. ✅ Upload more documents to knowledge base
5. 🎯 Share your phone number with users!

Your RAG Bot is now a **complete multi-modal AI assistant**! 🎉