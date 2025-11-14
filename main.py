from fastapi import FastAPI, File, UploadFile, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
import os
import logging
from config import Config
from rag_system import RAGSystem
from slack_bot import SlackBot
from whatsapp_bot import WhatsAppBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="RAG Bot API", description="RAG Bot with Slack and WhatsApp integration")

# Initialize components
config = Config()
rag_system = RAGSystem()

# Initialize bots (only if credentials are available)
slack_bot = None
whatsapp_bot = None

try:
    if config.SLACK_BOT_TOKEN and config.SLACK_SIGNING_SECRET:
        slack_bot = SlackBot()
        logger.info("Slack bot initialized successfully")
    else:
        logger.warning("Slack credentials not configured")
except Exception as e:
    logger.error(f"Failed to initialize Slack bot: {str(e)}")

try:
    whatsapp_bot = WhatsAppBot()
    logger.info("WhatsApp bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize WhatsApp bot: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Bot API is running!",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "query": "/query",
            "stats": "/stats",
            "slack": "/slack/events",
            "whatsapp": "/whatsapp/webhook"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_system": "operational",
        "slack_bot": "enabled" if slack_bot else "disabled",
        "whatsapp_bot": "enabled" if whatsapp_bot else "disabled"
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to the RAG system"""
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
        
        # Read file content
        content = await file.read()
        
        if file.content_type == "application/pdf":
            result = rag_system.add_pdf_document(content, file.filename)
            return {"message": result, "filename": file.filename}
        else:
            # Handle text files
            text_content = content.decode('utf-8')
            result = rag_system.add_document(text_content, {"filename": file.filename})
            return {"message": result, "filename": file.filename}
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_rag(request: dict):
    """Query the RAG system"""
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        response = rag_system.query(question)
        return {"question": question, "answer": response}
    
    except Exception as e:
        logger.error(f"Error querying RAG system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get RAG system statistics"""
    try:
        stats = rag_system.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/url")
async def research_url(request: dict):
    """Scrape a URL and add to knowledge base"""
    try:
        from web_research import WebResearcher
        researcher = WebResearcher()
        
        url = request.get("url", "")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        result = researcher.add_url_to_knowledge_base(url)
        return {"result": result, "url": url}
    
    except Exception as e:
        logger.error(f"Error researching URL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research/topic")
async def research_topic(request: dict):
    """Research a topic and add to knowledge base"""
    try:
        from web_research import WebResearcher
        researcher = WebResearcher()
        
        topic = request.get("topic", "")
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        num_sources = request.get("num_sources", 3)
        result = researcher.research_topic(topic, num_sources)
        return {"result": result, "topic": topic}
    
    except Exception as e:
        logger.error(f"Error researching topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Slack integration
if slack_bot:
    @app.post("/slack/events")
    async def slack_events(request: Request):
        """Handle Slack events"""
        return await slack_bot.get_handler().handle(request)

# WhatsApp integration
if whatsapp_bot:
    @app.post("/whatsapp/webhook")
    async def whatsapp_webhook(request: Request):
        """Handle WhatsApp webhook"""
        try:
            form_data = await request.form()
            from_number = form_data.get("From", "").replace("whatsapp:", "")
            message_body = form_data.get("Body", "")
            
            # Check for media attachments
            media_url = form_data.get("MediaUrl0", None)
            media_type = form_data.get("MediaContentType0", None)
            
            if media_url:
                logger.info(f"WhatsApp media from {from_number}: {media_type}")
            else:
                logger.info(f"WhatsApp message from {from_number}: {message_body}")
            
            # Process message with optional media
            response_text = whatsapp_bot.handle_message(from_number, message_body, media_url, media_type)
            
            # Return TwiML response
            twiml_response = whatsapp_bot.create_twiml_response(response_text)
            return PlainTextResponse(content=twiml_response, media_type="application/xml")
        
        except Exception as e:
            logger.error(f"Error handling WhatsApp webhook: {str(e)}")
            return PlainTextResponse(content="Error processing message", status_code=500)

# Voice integration
try:
    from voice_agent import VoiceAgent
    voice_agent = VoiceAgent()
    logger.info("Voice agent initialized successfully")
    
    @app.post("/voice/webhook")
    async def voice_webhook(request: Request):
        """Handle incoming voice calls"""
        try:
            form_data = await request.form()
            from_number = form_data.get("From", "")
            call_sid = form_data.get("CallSid", "")
            
            logger.info(f"Voice call from {from_number}, CallSid: {call_sid}")
            
            # Handle incoming call
            twiml_response = voice_agent.handle_incoming_call(from_number)
            return PlainTextResponse(content=twiml_response, media_type="application/xml")
        
        except Exception as e:
            logger.error(f"Error handling voice webhook: {str(e)}")
            return PlainTextResponse(content="<Response><Say>Error processing call</Say></Response>", media_type="application/xml")
    
    @app.post("/voice/process")
    async def voice_process(request: Request):
        """Process speech input from voice call"""
        try:
            form_data = await request.form()
            speech_result = form_data.get("SpeechResult", "")
            call_sid = form_data.get("CallSid", "")
            
            logger.info(f"Speech from {call_sid}: {speech_result}")
            
            # Check if this is a continuation decision
            if call_sid in getattr(voice_agent, 'continuation_mode', set()):
                twiml_response = voice_agent.handle_continue(speech_result)
            else:
                # Process the speech
                twiml_response = voice_agent.process_speech(speech_result, call_sid)
            
            return PlainTextResponse(content=twiml_response, media_type="application/xml")
        
        except Exception as e:
            logger.error(f"Error processing speech: {str(e)}")
            return PlainTextResponse(content="<Response><Say>Error processing speech</Say></Response>", media_type="application/xml")
    
    @app.post("/sms/webhook")
    async def sms_webhook(request: Request):
        """Handle SMS messages (separate from WhatsApp)"""
        try:
            form_data = await request.form()
            from_number = form_data.get("From", "")
            message_body = form_data.get("Body", "")
            
            logger.info(f"SMS from {from_number}: {message_body}")
            
            # Use same WhatsApp bot logic for SMS
            response_text = whatsapp_bot.handle_message(from_number, message_body)
            
            # Return TwiML response
            twiml_response = whatsapp_bot.create_twiml_response(response_text)
            return PlainTextResponse(content=twiml_response, media_type="application/xml")
        
        except Exception as e:
            logger.error(f"Error handling SMS webhook: {str(e)}")
            return PlainTextResponse(content="Error processing message", status_code=500)
    
except Exception as e:
    logger.error(f"Failed to initialize voice agent: {str(e)}")

if __name__ == "__main__":
    # Validate configuration
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        exit(1)
    
    # Create necessary directories
    os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
    
    logger.info(f"Starting RAG Bot API on port {config.PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=False,  # Disable reload for Raspberry Pi
        log_level="info"
    )