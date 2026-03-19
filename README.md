# RAG Bot with GPT-OSS Integration

A Retrieval-Augmented Generation (RAG) bot that integrates with GPT-OSS via Hugging Face and provides access via Slack and WhatsApp. The runtime now starts cleanly on low-resource machines by using a lightweight hashing embedder unless `sentence-transformers` is installed.

## Features

- 🤖 **RAG System**: Upload documents and query them using natural language
- 💬 **Slack Integration**: Access the bot directly from Slack
- 📱 **WhatsApp Integration**: Query via WhatsApp using Twilio
- 🔍 **Vector Search**: Powered by ChromaDB for efficient document retrieval
- 🧠 **AI Responses**: Uses GPT-OSS via Hugging Face for intelligent answers
- 🍓 **Low-Resource Startup**: Runs without pulling GPU-only `torch` dependencies by default
- 🔐 **Safer Defaults**: Optional API key protection, Twilio signature validation, and SSRF protections for scrape/media URLs

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

Recommended configuration:
- `API_KEY`: Protects REST endpoints such as `/upload`, `/query`, `/stats`, and `/research/*`
- `HUGGINGFACE_API_TOKEN`: Enables LLM-generated answers. Without it, the bot falls back to context excerpts.

Optional (for integrations):
- Slack: `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`
- WhatsApp: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- Public webhook deployments: `PUBLIC_BASE_URL`

### 3. Start
```bash
./start.sh
```

By default the app binds to `127.0.0.1`. Set `HOST=0.0.0.0` only when you intend to expose it behind a firewall or reverse proxy.

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
  -H "X-API-Key: your_api_key" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Query the System
```bash
curl -X POST "http://localhost:8000/query" \
  -H "X-API-Key: your_api_key" \
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
4. Keep `VALIDATE_TWILIO_SIGNATURES=true` in production

## Raspberry Pi Deployment

### System Requirements
- Raspberry Pi 4 (4GB+ RAM recommended)
- Python 3.10+
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
ExecStart=/home/pi/ragbot/.venv/bin/python main.py
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

1. **Large dependency installs**: The default install no longer requires `sentence-transformers`. If you want higher-quality embeddings, install it manually after the core app is working.
2. **Slow Responses**: Check network connection to Hugging Face
3. **ChromaDB Errors**: Ensure write permissions to `chroma_db` and `user_data` directories
4. **Import Errors**: Activate the virtual environment before running
5. **Webhook validation failures**: Set `PUBLIC_BASE_URL` so Twilio signature checks see the public URL Twilio calls

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
