import logging
import os
import secrets
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from twilio.request_validator import RequestValidator

from config import Config
from rag_system import RAGSystem
from security_utils import sanitize_filename
from slack_bot import SlackBot
from whatsapp_bot import WhatsAppBot
from web_research import WebResearcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = Config()

app = FastAPI(
    title="RAG Bot API",
    description="RAG Bot with Slack and WhatsApp integration",
    docs_url="/docs" if config.ENABLE_DOCS else None,
    redoc_url="/redoc" if config.ENABLE_DOCS else None,
    openapi_url="/openapi.json" if config.ENABLE_DOCS else None,
)

_rag_system: Optional[RAGSystem] = None
_slack_bot: Optional[SlackBot] = None
_whatsapp_bot: Optional[WhatsAppBot] = None
_voice_agent = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class UrlResearchRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class TopicResearchRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=256)
    num_sources: int = Field(default=3, ge=1, le=10)


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
    if not config.API_KEY:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


def get_rag_system() -> RAGSystem:
    global _rag_system
    if _rag_system is None:
        try:
            _rag_system = RAGSystem()
        except Exception as exc:
            logger.exception("Failed to initialize RAG system")
            raise HTTPException(status_code=503, detail="RAG system unavailable") from exc
    return _rag_system


def get_slack_bot() -> Optional[SlackBot]:
    global _slack_bot
    if not config.SLACK_BOT_TOKEN or not config.SLACK_SIGNING_SECRET:
        return None
    if _slack_bot is None:
        try:
            _slack_bot = SlackBot()
        except Exception:
            logger.exception("Failed to initialize Slack bot")
            return None
    return _slack_bot


def get_whatsapp_bot() -> Optional[WhatsAppBot]:
    global _whatsapp_bot
    if _whatsapp_bot is None:
        try:
            _whatsapp_bot = WhatsAppBot()
        except Exception:
            logger.exception("Failed to initialize WhatsApp bot")
            return None
    return _whatsapp_bot


def get_voice_agent():
    global _voice_agent
    if _voice_agent is None:
        try:
            from voice_agent import VoiceAgent

            _voice_agent = VoiceAgent()
        except Exception:
            logger.exception("Failed to initialize voice agent")
            return None
    return _voice_agent


def build_public_request_url(request: Request) -> str:
    if config.PUBLIC_BASE_URL:
        base = config.PUBLIC_BASE_URL.rstrip("/")
        query = f"?{request.url.query}" if request.url.query else ""
        return f"{base}{request.url.path}{query}"
    return str(request.url)


def validate_twilio_request(request: Request, form_data):
    if not config.VALIDATE_TWILIO_SIGNATURES or not config.TWILIO_AUTH_TOKEN:
        return

    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        raise HTTPException(status_code=403, detail="Missing Twilio signature")

    validator = RequestValidator(config.TWILIO_AUTH_TOKEN)
    if not validator.validate(build_public_request_url(request), dict(form_data), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")


@app.get("/")
async def root():
    return {
        "message": "RAG Bot API is running",
        "endpoints": {
            "health": "/health",
            "upload": "/upload",
            "query": "/query",
            "stats": "/stats",
            "slack": "/slack/events",
            "whatsapp": "/whatsapp/webhook",
        },
    }


@app.get("/health")
async def health_check():
    rag_status = "operational"
    try:
        rag_stats = get_rag_system().get_collection_stats()
    except HTTPException:
        rag_status = "degraded"
        rag_stats = {}

    return {
        "status": "healthy" if rag_status == "operational" else "degraded",
        "rag_system": rag_status,
        "slack_bot": "enabled" if get_slack_bot() else "disabled",
        "whatsapp_bot": "enabled" if get_whatsapp_bot() else "disabled",
        "docs": "enabled" if config.ENABLE_DOCS else "disabled",
        "rag_details": rag_stats,
    }


@app.post("/upload", dependencies=[Depends(require_api_key)])
async def upload_document(file: UploadFile = File(...)):
    try:
        os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
        filename = sanitize_filename(file.filename)
        content = await file.read()

        if len(content) > config.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds upload size limit")

        if file.content_type == "application/pdf" or filename.lower().endswith(".pdf"):
            result = get_rag_system().add_pdf_document(content, filename)
            return {"message": result, "filename": filename}

        if file.content_type not in {"text/plain", "application/json", "text/markdown"} and not (
            filename.lower().endswith((".txt", ".md", ".json"))
        ):
            raise HTTPException(status_code=400, detail="Only PDF and text-based uploads are supported")

        text_content = content.decode("utf-8", errors="strict")
        if len(text_content) > config.MAX_TEXT_CHARS:
            raise HTTPException(status_code=413, detail="Text file exceeds maximum supported size")

        result = get_rag_system().add_document(text_content, {"filename": filename, "type": "text"})
        return {"message": result, "filename": filename}
    except HTTPException:
        raise
    except UnicodeDecodeError as exc:
        logger.warning("Rejected non-UTF8 text upload: %s", exc)
        raise HTTPException(status_code=400, detail="Uploaded text files must be UTF-8 encoded") from exc
    except Exception as exc:
        logger.exception("Error uploading document")
        raise HTTPException(status_code=500, detail="Failed to upload document") from exc


@app.post("/query", dependencies=[Depends(require_api_key)])
async def query_rag(request: QueryRequest):
    try:
        response = get_rag_system().query(request.question)
        return {"question": request.question, "answer": response}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error querying RAG system")
        raise HTTPException(status_code=500, detail="Failed to process query") from exc


@app.get("/stats", dependencies=[Depends(require_api_key)])
async def get_stats():
    try:
        return get_rag_system().get_collection_stats()
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting stats")
        raise HTTPException(status_code=500, detail="Failed to get stats") from exc


@app.post("/research/url", dependencies=[Depends(require_api_key)])
async def research_url(request: UrlResearchRequest):
    try:
        researcher = WebResearcher()
        result = researcher.add_url_to_knowledge_base(request.url)
        return {"result": result, "url": request.url}
    except Exception as exc:
        logger.exception("Error researching URL")
        raise HTTPException(status_code=500, detail="Failed to research URL") from exc


@app.post("/research/topic", dependencies=[Depends(require_api_key)])
async def research_topic(request: TopicResearchRequest):
    try:
        researcher = WebResearcher()
        result = researcher.research_topic(request.topic, request.num_sources)
        return {"result": result, "topic": request.topic}
    except Exception as exc:
        logger.exception("Error researching topic")
        raise HTTPException(status_code=500, detail="Failed to research topic") from exc


@app.post("/slack/events")
async def slack_events(request: Request):
    slack_bot = get_slack_bot()
    if not slack_bot:
        raise HTTPException(status_code=503, detail="Slack integration not configured")
    return await slack_bot.get_handler().handle(request)


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    whatsapp_bot = get_whatsapp_bot()
    if not whatsapp_bot:
        return PlainTextResponse(content="WhatsApp integration unavailable", status_code=503)

    try:
        form_data = await request.form()
        validate_twilio_request(request, form_data)

        from_number = form_data.get("From", "").replace("whatsapp:", "")
        message_body = form_data.get("Body", "")
        media_url = form_data.get("MediaUrl0")
        media_type = form_data.get("MediaContentType0")

        logger.info("WhatsApp webhook received from %s", from_number or "unknown")
        response_text = whatsapp_bot.handle_message(from_number, message_body, media_url, media_type)
        return PlainTextResponse(
            content=whatsapp_bot.create_twiml_response(response_text),
            media_type="application/xml",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error handling WhatsApp webhook")
        return PlainTextResponse(content="Error processing message", status_code=500)


@app.post("/voice/webhook")
async def voice_webhook(request: Request):
    voice_agent = get_voice_agent()
    if not voice_agent:
        return PlainTextResponse(
            content="<Response><Say>Voice integration unavailable</Say></Response>",
            media_type="application/xml",
            status_code=503,
        )

    try:
        form_data = await request.form()
        validate_twilio_request(request, form_data)

        from_number = form_data.get("From", "")
        call_sid = form_data.get("CallSid", "")
        logger.info("Voice call from %s (%s)", from_number or "unknown", call_sid or "no-call-sid")
        return PlainTextResponse(
            content=voice_agent.handle_incoming_call(from_number),
            media_type="application/xml",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error handling voice webhook")
        return PlainTextResponse(
            content="<Response><Say>Error processing call</Say></Response>",
            media_type="application/xml",
        )


@app.post("/voice/process")
async def voice_process(request: Request):
    voice_agent = get_voice_agent()
    if not voice_agent:
        return PlainTextResponse(
            content="<Response><Say>Voice integration unavailable</Say></Response>",
            media_type="application/xml",
            status_code=503,
        )

    try:
        form_data = await request.form()
        validate_twilio_request(request, form_data)

        speech_result = form_data.get("SpeechResult", "")
        call_sid = form_data.get("CallSid", "")
        logger.info("Speech received for call %s", call_sid or "unknown")

        if call_sid in getattr(voice_agent, "continuation_mode", set()):
            twiml_response = voice_agent.handle_continue(speech_result)
        else:
            twiml_response = voice_agent.process_speech(speech_result, call_sid)

        return PlainTextResponse(content=twiml_response, media_type="application/xml")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error processing speech")
        return PlainTextResponse(
            content="<Response><Say>Error processing speech</Say></Response>",
            media_type="application/xml",
        )


@app.post("/sms/webhook")
async def sms_webhook(request: Request):
    whatsapp_bot = get_whatsapp_bot()
    if not whatsapp_bot:
        return PlainTextResponse(content="SMS integration unavailable", status_code=503)

    try:
        form_data = await request.form()
        validate_twilio_request(request, form_data)

        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "")
        logger.info("SMS received from %s", from_number or "unknown")
        response_text = whatsapp_bot.handle_message(from_number, message_body)
        return PlainTextResponse(
            content=whatsapp_bot.create_twiml_response(response_text),
            media_type="application/xml",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error handling SMS webhook")
        return PlainTextResponse(content="Error processing message", status_code=500)


if __name__ == "__main__":
    try:
        config.validate()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        raise SystemExit(1) from exc

    os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(config.USER_DATA_DIRECTORY, exist_ok=True)

    logger.info("Starting RAG Bot API on %s:%s", config.HOST, config.PORT)
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info",
    )
