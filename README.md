# RAG Bot with GPT-OSS Integration

A Retrieval-Augmented Generation (RAG) bot that integrates with GPT-OSS via Hugging Face and provides access via Slack and WhatsApp. Optimized for Raspberry Pi deployment.

## Features

- 🤖 **RAG System**: Upload documents and query them using natural language
- 💬 **Slack Integration**: Access the bot directly from Slack
- 📱 **WhatsApp Integration**: Query via WhatsApp using Twilio
- 🔍 **Vector Search**: Powered by ChromaDB for efficient document retrieval
- 🧠 **AI Responses**: Uses GPT-OSS via Hugging Face for intelligent answers
- 🍓 **Raspberry Pi Ready**: Optimized for low-resource environments

## Quick Start

### 1. Setup
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Configure
Edit `.env` file with your credentials:
```bash
cp .env.example .env
nano .env
```

Required configuration:
- `HUGGINGFACE_API_TOKEN`: Your Hugging Face API token

Optional (for integrations):
- Slack: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- WhatsApp: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`

### 3. Start
```bash
./start.sh
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /upload` - Upload documents (PDF or text)
- `POST /query` - Query the RAG system
- `GET /stats` - Get knowledge base statistics
- `POST /slack/events` - Slack webhook
- `POST /whatsapp/webhook` - WhatsApp webhook

## Usage Examples

### Upload a Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Query the System
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

## Slack Setup

1. Create a Slack app at https://api.slack.com/apps
2. Add bot token scopes: `app_mentions:read`, `chat:write`, `files:read`
3. Enable events: `app_mention`, `file_shared`
4. Set event request URL: `https://your-domain.com/slack/events`
5. Install app to workspace

## WhatsApp Setup

1. Create Twilio account at https://www.twilio.com
2. Set up WhatsApp sandbox or get approved number
3. Configure webhook URL: `https://your-domain.com/whatsapp/webhook`

## Raspberry Pi Deployment

### System Requirements
- Raspberry Pi 4 (4GB+ RAM recommended)
- Python 3.8+
- 16GB+ SD card

### Performance Tips
- Use SSD instead of SD card for better I/O
- Increase swap space if needed
- Monitor temperature and use cooling

### Auto-start Service
Create systemd service:
```bash
sudo nano /etc/systemd/system/ragbot.service
```

```ini
[Unit]
Description=RAG Bot Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ragbot
ExecStart=/home/pi/ragbot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ragbot.service
sudo systemctl start ragbot.service
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack/WhatsApp│    │   FastAPI App   │    │   FlexaAI API   │
│                 │───▶│                 │───▶│                 │
│   User Input    │    │   RAG System    │    │   GPT-OSS-120B  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   ChromaDB      │
                       │   Vector Store  │
                       └─────────────────┘
```

## Troubleshooting

### Common Issues

1. **Memory Issues on Pi**: Reduce `CHUNK_SIZE` in config.py
2. **Slow Responses**: Check network connection to Hugging Face
3. **ChromaDB Errors**: Ensure write permissions to `chroma_db` directory
4. **Import Errors**: Activate virtual environment before running
5. **GPT-OSS API Errors**: Verify your Hugging Face token has access to the model

### Logs
Check application logs:
```bash
tail -f logs/ragbot.log
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test on Raspberry Pi
5. Submit pull request

## License

MIT License - see LICENSE file for details.