"""
WhatsApp Bot using Infobip (replaces Twilio)
"""
from infobip_client import InfobipClient
from rag_system import RAGSystem
from user_rag_system import UserRAGSystem
from user_manager import UserManager
from config import Config
import logging
import requests

logger = logging.getLogger(__name__)


class WhatsAppBotInfobip:
    def __init__(self):
        self.config = Config()
        self.rag_system = RAGSystem()
        self.user_rag_system = UserRAGSystem()
        self.user_manager = UserManager()

        # Initialize Infobip client
        infobip_api_key = getattr(self.config, 'INFOBIP_API_KEY', None)
        infobip_sender = getattr(self.config, 'INFOBIP_WHATSAPP_NUMBER', None)

        if infobip_api_key and infobip_sender:
            self.infobip_client = InfobipClient(infobip_api_key)
            self.sender_number = infobip_sender
            logger.info("✅ Infobip WhatsApp client initialized")
        else:
            self.infobip_client = None
            logger.warning("❌ Infobip credentials not configured")

    def handle_incoming_message(self, webhook_data: dict) -> dict:
        """
        Handle incoming Infobip WhatsApp webhook

        Infobip webhook format:
        {
            "results": [{
                "from": "447123456789",
                "to": "441234567890",
                "receivedAt": "2024-01-01T12:00:00.000+0000",
                "messageId": "...",
                "message": {
                    "text": "Hello"
                }
            }]
        }
        """
        try:
            results = webhook_data.get("results", [])
            if not results:
                return {"status": "no_messages"}

            responses = []
            for result in results:
                from_number = result.get("from")
                message_data = result.get("message", {})
                message_text = message_data.get("text", "")

                # Handle the message
                response_text = self.handle_message(from_number, message_text)

                # Send response via Infobip
                self.send_message(from_number, response_text)

                responses.append({
                    "from": from_number,
                    "response": response_text
                })

            return {"status": "success", "responses": responses}

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {"status": "error", "message": str(e)}

    def handle_message(self, from_number: str, message_body: str) -> str:
        """Handle incoming WhatsApp message"""
        try:
            # Get or create user
            user = self.user_manager.get_or_create_user(from_number)
            user_id = user["user_id"]

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

            else:
                # Regular query with conversation context
                response = self.user_rag_system.query_with_context(user_id, message_body)
                return f"🤖 {response}"

        except Exception as e:
            logger.error(f"Error handling WhatsApp message: {str(e)}")
            return "Sorry, I encountered an error processing your message. Please try again."

    def send_message(self, to: str, message: str):
        """Send WhatsApp message via Infobip"""
        if not self.infobip_client:
            logger.error("Infobip client not initialized")
            return

        try:
            response = self.infobip_client.send_whatsapp_message(
                to=to,
                message=message,
                from_number=self.sender_number
            )
            logger.info(f"Message sent to {to}")
            return response
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def send_interactive_menu(self, to: str):
        """Send interactive button menu"""
        buttons = [
            {"id": "stats", "title": "📊 My Stats"},
            {"id": "help", "title": "❓ Help"},
            {"id": "clear", "title": "🗑️ Clear History"}
        ]

        try:
            response = self.infobip_client.send_whatsapp_interactive_button(
                to=to,
                from_number=self.sender_number,
                body_text="What would you like to do?",
                buttons=buttons,
                header_text="HeySalad AI Assistant",
                footer_text="Powered by RAG + GPT-OSS"
            )
            return response
        except Exception as e:
            logger.error(f"Failed to send interactive menu: {e}")

    def _get_welcome_message(self, name: str) -> str:
        """Get welcome message"""
        return f"""👋 Welcome {name}!

I'm your AI assistant powered by RAG and GPT-OSS.

Ask me anything about:
• Documents in my knowledge base
• General questions
• Research topics

Commands:
• 'help' - Show help
• 'stats' - View your stats
• 'clear' - Clear conversation

What can I help you with?"""

    def _get_help_message(self) -> str:
        """Get help message"""
        return """🤖 *How to use me:*

*Ask Questions:*
Just type your question naturally!

*Commands:*
• help - Show this message
• stats - Your usage statistics
• clear - Clear conversation history

*Special Features:*
• research [topic] - Deep research
• scrape [url] - Extract website content

Try asking me something! 🚀"""

    def _get_user_stats_message(self, user_id: str) -> str:
        """Get user statistics"""
        try:
            stats = self.user_rag_system.get_user_stats(user_id)
            return f"""📊 *Your Statistics*

• Documents uploaded: {stats.get('documents', 0)}
• Questions asked: {stats.get('queries', 0)}
• KB size: {stats.get('kb_size', 'N/A')}

Keep asking questions! 💪"""
        except Exception as e:
            return f"Error getting stats: {str(e)}"


if __name__ == "__main__":
    # Test the bot
    logging.basicConfig(level=logging.INFO)

    bot = WhatsAppBotInfobip()
    print("✅ WhatsApp Bot (Infobip) initialized")

    # Test message handling
    test_message = bot.handle_message("447123456789", "hello")
    print(f"\nTest response:\n{test_message}")
