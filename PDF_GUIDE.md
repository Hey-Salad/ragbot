# 📄 PDF Processing Guide for RAG Bot

## How It Works

Your RAG bot **already supports PDF uploads** via WhatsApp! Here's how the system processes PDFs:

### The Flow:

1. **User sends PDF** → WhatsApp/Twilio receives it
2. **Bot downloads PDF** → Using Twilio's media URL with authentication
3. **Extract text** → PyPDF2 extracts all text from every page
4. **Chunk & embed** → Text is split into chunks and converted to embeddings
5. **Store in user's KB** → Added to the user's private ChromaDB collection
6. **Ready to query** → User can now ask questions about the PDF!

## How to Use (WhatsApp)

### Upload a PDF:
1. Open WhatsApp chat with your bot
2. Click the attachment icon (📎)
3. Select "Document" and choose your PDF
4. Send it!

The bot will respond:
```
📄 PDF Uploaded Successfully!

Added 15 chunks to your private knowledge base

💡 You can now ask me questions about this document!
```

### Ask Questions:
After uploading, just ask questions naturally:
- "What is this document about?"
- "Summarize the main points"
- "Tell me about section 3"
- "What does it say about machine learning?"

## Supported File Types

✅ **PDF** - Fully supported with text extraction  
✅ **Text files** (.txt) - Directly processed  
❌ **Images** - Not yet supported (coming soon)  
❌ **Word docs** - Not yet supported

## Technical Details

### PDF Processing Code
Located in `whatsapp_bot.py`:

```python
def _handle_media_upload(self, user_id: str, media_url: str, media_type: str):
    # Downloads PDF from Twilio
    # Extracts text using PyPDF2
    # Adds to user's private knowledge base
    # Returns confirmation message
```

### Key Features:

1. **Per-User Storage**: Each user has their own private ChromaDB collection
2. **Conversation Memory**: Bot remembers context from previous messages
3. **Chunking**: Large PDFs are split into manageable chunks for better retrieval
4. **Embeddings**: Uses `all-MiniLM-L6-v2` for semantic search
5. **AI Responses**: GPT-OSS generates natural language answers

## Testing PDF Upload

Run the test script:
```bash
source venv/bin/activate
python test_pdf_upload.py
```

This will:
- Create a test user
- Upload sample PDF content
- Run 4 test queries
- Show statistics

## Troubleshooting

### PDF not processing?

1. **Check logs**: Look at server output for errors
2. **File size**: Very large PDFs may timeout (increase timeout in code)
3. **Scanned PDFs**: If PDF is just images, text extraction won't work
4. **Authentication**: Ensure Twilio credentials are correct in `.env`

### Check if it's working:

```bash
# Check server logs
tail -f logs/ragbot.log

# Test the API directly
curl -X POST http://localhost:8000/upload \
  -F "file=@your_document.pdf"
```

### Common Issues:

**"Failed to download the file"**
- Twilio authentication issue
- Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env

**"Error processing PDF"**
- PDF might be corrupted
- PDF might be image-based (scanned document)
- Try a different PDF

**No response after upload**
- Check if server is running: `curl http://localhost:8000/health`
- Check ChromaDB is working: `curl http://localhost:8000/stats`

## API Endpoints

You can also upload PDFs via the REST API:

```bash
# Upload PDF
curl -X POST http://localhost:8000/upload \
  -F "file=@document.pdf"

# Query the knowledge base
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this about?"}'
```

## How GPT-OSS Processes PDFs

**Important**: GPT-OSS (and most LLMs) **cannot directly read PDFs**. Instead:

1. **Text Extraction**: PyPDF2 extracts text from PDF
2. **Semantic Search**: Your question is embedded and matched against PDF chunks
3. **Context Building**: Top 5 most relevant chunks are retrieved
4. **AI Generation**: GPT-OSS reads the TEXT chunks and generates an answer

This is called **RAG (Retrieval Augmented Generation)**:
- **Retrieval**: Find relevant text from your PDF
- **Augmented**: Add that text as context
- **Generation**: LLM generates answer based on context

## Example Workflow

```
User: [Sends ML_Guide.pdf]
Bot: 📄 PDF Uploaded! Added 23 chunks to your KB

User: "What are the best practices for data preprocessing?"
Bot: [Searches PDF chunks] → [Finds relevant sections] → [Generates answer]
     "Based on your document, best practices include:
      1. Handle missing values
      2. Scale features
      3. Encode categorical variables..."

User: "Tell me more about feature scaling"
Bot: [Remembers conversation] → [Searches PDF] → [Generates contextual answer]
     "As mentioned earlier, feature scaling is important because..."
```

## Advanced Features

### Research Mode
```
User: "research machine learning best practices"
Bot: [Scrapes web] → [Adds to your KB] → [Confirms]
```

### URL Scraping
```
User: "scrape https://example.com/article"
Bot: [Downloads page] → [Extracts text] → [Adds to KB]
```

### Conversation Memory
The bot remembers your conversation:
```
User: "What's in my PDF?"
Bot: "Your PDF discusses machine learning..."

User: "Tell me more about that"
Bot: [Remembers "that" = machine learning] → [Provides details]
```

### Clear History
```
User: "clear"
Bot: "✅ Conversation history cleared! Starting fresh."
```

## Privacy & Security

- ✅ Each user has a **private** knowledge base
- ✅ Your PDFs are **not shared** with other users
- ✅ Phone numbers are **hashed** for privacy
- ✅ Conversation history is **per-user**
- ✅ Data stored locally on your server

## Next Steps

Want to improve PDF processing?

1. **Add OCR**: For scanned PDFs (use `pytesseract`)
2. **Add images**: Extract and describe images (use vision models)
3. **Add Word docs**: Support .docx files (use `python-docx`)
4. **Better chunking**: Use semantic chunking instead of fixed-size
5. **Metadata extraction**: Extract title, author, date from PDFs

## Questions?

Your RAG bot is fully functional and ready to process PDFs! Just send a PDF via WhatsApp and start asking questions.
