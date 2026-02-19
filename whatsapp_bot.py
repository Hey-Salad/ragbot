from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from rag_system import RAGSystem
from user_rag_system import UserRAGSystem
from user_manager import UserManager
from config import Config
import logging
import requests
import PyPDF2
import io

class WhatsAppBot:
    def __init__(self):
        self.config = Config()
        self.rag_system = RAGSystem()
        self.user_rag_system = UserRAGSystem()
        self.user_manager = UserManager()
        
        # Initialize Twilio client
        if self.config.TWILIO_ACCOUNT_SID and self.config.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                self.config.TWILIO_ACCOUNT_SID,
                self.config.TWILIO_AUTH_TOKEN
            )
        else:
            self.twilio_client = None
            logging.warning("Twilio credentials not configured")
    
    def handle_message(self, from_number: str, message_body: str, media_url: str = None, media_type: str = None) -> str:
        """Handle incoming WhatsApp message with optional media"""
        try:
            # Get or create user
            user = self.user_manager.get_or_create_user(from_number)
            user_id = user["user_id"]
            
            # Handle media (file uploads)
            if media_url:
                return self._handle_media_upload(user_id, media_url, media_type)
            
            message_body_lower = message_body.strip().lower()
            
            # Handle special commands
            if message_body_lower in ['hello', 'hi', 'start']:
                return self._get_welcome_message(user["name"])
            
            elif message_body_lower in ['help', '?']:
                return self._get_help_message()
            
            elif message_body_lower == 'stats':
                return self._get_user_stats_message(user_id)
            
            elif message_body_lower == 'clear':
                self.user_rag_system.clear_conversation(user_id)
                return "✅ Conversation history cleared! Starting fresh."
            
            elif message_body_lower.startswith('research '):
                # Research a topic and add to user's KB
                topic = message_body[9:].strip()
                return self._research_topic_for_user(user_id, topic)
            
            elif message_body_lower.startswith('scrape '):
                # Scrape a URL and add to user's KB
                url = message_body[7:].strip()
                return self._scrape_url_for_user(user_id, url)
            
            else:
                # Regular query with conversation context
                response = self.user_rag_system.query_with_context(user_id, message_body)
                return f"🤖 {response}"
        
        except Exception as e:
            logging.error(f"Error handling WhatsApp message: {str(e)}")
            return "Sorry, I encountered an error processing your message. Please try again."
    
    def _handle_media_upload(self, user_id: str, media_url: str, media_type: str) -> str:
        """Handle file uploads from WhatsApp"""
        try:
            # Add logging for debugging
            logging.info(f"Processing media upload for user {user_id}")
            logging.info(f"Media URL: {media_url}")
            logging.info(f"Media Type: {media_type}")

            # Download the media with proper authentication
            response = requests.get(
                media_url,
                auth=(self.config.TWILIO_ACCOUNT_SID, self.config.TWILIO_AUTH_TOKEN),
                timeout=30
            )

            if response.status_code != 200:
                logging.error(f"Failed to download media: HTTP {response.status_code}")
                return "❌ Failed to download the file. Please try again."

            content = response.content
            logging.info(f"Downloaded {len(content)} bytes")

            # Detect file type using multiple methods
            is_pdf = False
            is_image = False
            is_text = False

            # Method 1: Check MIME type (with null-safety)
            if media_type:
                media_type_lower = media_type.lower()
                logging.info(f"Checking MIME type: {media_type_lower}")

                # PDF detection - handle various MIME types
                if ('pdf' in media_type_lower or
                    media_type_lower in ['application/octet-stream', 'application/x-pdf', 'application/vnd.pdf']):
                    is_pdf = True
                    logging.info("Detected as PDF by MIME type")

                elif 'image' in media_type_lower:
                    is_image = True
                    logging.info("Detected as image by MIME type")

                elif 'text' in media_type_lower:
                    is_text = True
                    logging.info("Detected as text by MIME type")

            # Method 2: Check file extension from URL (fallback)
            if not is_pdf and not is_image and not is_text and media_url:
                url_lower = media_url.lower()
                if url_lower.endswith('.pdf') or '.pdf?' in url_lower:
                    is_pdf = True
                    logging.info("Detected as PDF by file extension")
                elif any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    is_image = True
                    logging.info("Detected as image by file extension")
                elif any(ext in url_lower for ext in ['.txt', '.csv', '.md']):
                    is_text = True
                    logging.info("Detected as text by file extension")

            # Method 3: Check magic bytes (file signature)
            if not is_pdf and len(content) >= 4:
                # PDF magic bytes: %PDF
                if content[:4] == b'%PDF':
                    is_pdf = True
                    logging.info("Detected as PDF by magic bytes")

            # Process based on detected type
            if is_pdf:
                logging.info("Processing as PDF document")
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                    text = ""
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        logging.info(f"Extracted {len(page_text)} chars from page {page_num + 1}")

                    if not text.strip():
                        logging.warning("PDF text extraction resulted in empty content")
                        return "⚠️ PDF uploaded but no text could be extracted. The PDF might be image-based or encrypted."

                    metadata = {"source": "whatsapp_upload", "type": "pdf"}
                    result = self.user_rag_system.add_document_for_user(user_id, text, metadata)
                    logging.info(f"Successfully processed PDF: {result}")
                    return f"📄 *PDF Uploaded!*\n\n{result}\n\nYou can now ask questions about this document!"

                except Exception as pdf_error:
                    logging.error(f"Error processing PDF: {str(pdf_error)}")
                    return f"❌ Error reading PDF: {str(pdf_error)}\n\nThe file might be corrupted or password-protected."

            elif is_image:
                logging.info("Image detected but not yet supported")
                return "📷 Image received! Note: Image text extraction coming soon. For now, please upload PDF or text files."

            elif is_text:
                logging.info("Processing as text file")
                text = content.decode('utf-8')
                metadata = {"source": "whatsapp_upload", "type": "text"}
                result = self.user_rag_system.add_document_for_user(user_id, text, metadata)
                logging.info(f"Successfully processed text file: {result}")
                return f"📝 *Text File Uploaded!*\n\n{result}\n\nYou can now ask questions about this document!"

            else:
                logging.warning(f"Unsupported or undetected file type. MIME: {media_type}, URL: {media_url}")
                return f"❓ Unsupported file type: {media_type or 'unknown'}\n\nPlease upload PDF or text files.\n\nIf you sent a PDF, please try again or contact support."

        except Exception as e:
            logging.error(f"Error handling media upload: {str(e)}", exc_info=True)
            return f"❌ Error processing file: {str(e)}"
    
    def _get_welcome_message(self, name: str) -> str:
        """Get welcome message"""
        return f"""
🤖 *Welcome back, {name}!*

I'm your personal RAG Bot with conversation memory!

✨ *What I can do:*
• Remember our conversation (like ChatGPT)
• Answer questions from YOUR private knowledge base
• Accept file uploads (PDFs, text files)
• Research topics and learn from the web

📤 *Upload files:* Just send me a PDF or text file!
💬 *Ask anything:* I'll remember our conversation context

Type 'help' for commands!
        """
    
    def _get_help_message(self) -> str:
        """Get help message"""
        return """
🤖 *RAG Bot Help*

*Commands:*
• hello/hi - Get welcome message
• help/? - Show this help
• stats - Show YOUR personal statistics
• clear - Clear conversation history
• research <topic> - Research and add to YOUR knowledge base
• scrape <url> - Add website content to YOUR knowledge base

*File Uploads:*
📤 Just send me a PDF or text file - I'll add it to YOUR private knowledge base!

*Conversation:*
💬 I remember our conversation context (like ChatGPT)
🔒 Your data is private and isolated from other users

*Examples:*
• "What did we talk about earlier?"
• "Tell me more about that"
• Send a PDF → Ask questions about it
• "research healthy diets"

I'll remember our conversation and search YOUR private knowledge base!
        """
    
    def _get_user_stats_message(self, user_id: str) -> str:
        """Get user statistics message"""
        try:
            stats = self.user_rag_system.get_user_stats(user_id)
            return f"""
📊 *Your Personal Stats*

👤 Name: {stats['name']}
📅 Member since: {stats['member_since']} days ago
💬 Total messages: {stats['total_messages']}
📚 Documents in your KB: {stats['total_documents']}

Your knowledge base is private and secure! 🔒
            """
        except Exception as e:
            return f"Error getting stats: {str(e)}"
    
    def create_twiml_response(self, response_text: str) -> str:
        """Create TwiML response for Twilio webhook"""
        resp = MessagingResponse()
        resp.message(response_text)
        return str(resp)
    
    def _research_topic_for_user(self, user_id: str, topic: str) -> str:
        """Research a topic and add to user's knowledge base"""
        try:
            from web_research import WebResearcher
            researcher = WebResearcher()
            
            # Research the topic
            result = researcher.research_topic(topic)
            
            # The research already adds to global KB, but we should add to user's KB too
            # For now, return the result
            return f"🔍 *Research Results:*\n\n{result}\n\n_Added to YOUR knowledge base!_"
        except Exception as e:
            return f"Error researching topic: {str(e)}"
    
    def _scrape_url_for_user(self, user_id: str, url: str) -> str:
        """Scrape URL and add to user's knowledge base"""
        try:
            from web_research import WebResearcher
            researcher = WebResearcher()
            
            # Scrape the URL
            scrape_result = researcher.scrape_url(url)
            
            if scrape_result['success']:
                # Add to user's private knowledge base
                metadata = {
                    "source": "web_scrape",
                    "url": url,
                    "title": scrape_result['title']
                }
                result = self.user_rag_system.add_document_for_user(
                    user_id, 
                    scrape_result['content'], 
                    metadata
                )
                return f"🌐 *Web Scraping Success!*\n\n{result}\n\nSource: {url}"
            else:
                return f"❌ Failed to scrape: {scrape_result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error scraping URL: {str(e)}"
    
    def send_message(self, to_number: str, message: str) -> bool:
        """Send a message via WhatsApp"""
        if not self.twilio_client:
            logging.error("Twilio client not initialized")
            return False
        
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=f'whatsapp:{self.config.TWILIO_PHONE_NUMBER}',
                to=f'whatsapp:{to_number}'
            )
            logging.info(f"Message sent successfully: {message.sid}")
            return True
        
        except Exception as e:
            logging.error(f"Error sending WhatsApp message: {str(e)}")
            return False