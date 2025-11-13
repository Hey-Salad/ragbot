from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from rag_system import RAGSystem
from config import Config
import logging

class WhatsAppBot:
    def __init__(self):
        self.config = Config()
        self.rag_system = RAGSystem()
        
        # Initialize Twilio client
        if self.config.TWILIO_ACCOUNT_SID and self.config.TWILIO_AUTH_TOKEN:
            self.twilio_client = Client(
                self.config.TWILIO_ACCOUNT_SID,
                self.config.TWILIO_AUTH_TOKEN
            )
        else:
            self.twilio_client = None
            logging.warning("Twilio credentials not configured")
    
    def handle_message(self, from_number: str, message_body: str) -> str:
        """Handle incoming WhatsApp message"""
        try:
            message_body = message_body.strip().lower()
            
            # Handle special commands
            if message_body in ['hello', 'hi', 'start']:
                return self._get_welcome_message()
            
            elif message_body in ['help', '?']:
                return self._get_help_message()
            
            elif message_body == 'stats':
                return self._get_stats_message()
            
            else:
                # Regular query
                response = self.rag_system.query(message_body)
                return f"🤖 *RAG Bot Response:*\n\n{response}\n\n_Powered by GPT-OSS_"
        
        except Exception as e:
            logging.error(f"Error handling WhatsApp message: {str(e)}")
            return "Sorry, I encountered an error processing your message. Please try again."
    
    def _get_welcome_message(self) -> str:
        """Get welcome message"""
        return """
🤖 *Welcome to RAG Bot!*

I can help you find information from my knowledge base. 

Send me any question and I'll search through uploaded documents to provide you with relevant answers.

Type 'help' for more information or just ask me anything!
        """
    
    def _get_help_message(self) -> str:
        """Get help message"""
        return """
🤖 *RAG Bot Help*

*Commands:*
• hello/hi - Get welcome message
• help/? - Show this help
• stats - Show knowledge base statistics

*Usage:*
Just send me any question about topics in the knowledge base!

Examples:
• "What is machine learning?"
• "How does neural networks work?"
• "Explain quantum computing"

I'll search through all uploaded documents to find the best answer for you!
        """
    
    def _get_stats_message(self) -> str:
        """Get statistics message"""
        try:
            stats = self.rag_system.get_collection_stats()
            return f"""
📊 *Knowledge Base Stats*

• Document chunks: {stats['total_documents']}
• Collection: {stats['collection_name']}

Ready to answer your questions!
            """
        except Exception as e:
            return f"Error getting stats: {str(e)}"
    
    def create_twiml_response(self, response_text: str) -> str:
        """Create TwiML response for Twilio webhook"""
        resp = MessagingResponse()
        resp.message(response_text)
        return str(resp)
    
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