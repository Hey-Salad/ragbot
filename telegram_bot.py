"""
Telegram Bot for RAGbot
Using python-telegram-bot library
"""
import os
import logging
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from user_rag_system import UserRAGSystem
from user_manager import UserManager
from config import Config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self):
        self.config = Config()
        self.rag_system = UserRAGSystem()
        self.user_manager = UserManager()

        # Get Telegram token from config or env
        self.token = getattr(self.config, 'TELEGRAM_BOT_TOKEN', None) or os.getenv('TELEGRAM_BOT_TOKEN')

        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in config or environment")

        # Build application
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self._setup_handlers()

        logger.info("Telegram bot initialized")

    def _setup_handlers(self):
        """Setup command and message handlers"""

        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("clear", self.clear_command))

        # Messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        # Documents
        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_document)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        user_id = str(user.id)

        # Create user in system
        self.user_manager.get_or_create_user(user_id, name=user.first_name)

        welcome_message = f"""👋 Welcome {user.first_name}!

I'm your AI assistant powered by RAG and DeepSeek R1.

**What I can do:**
• Answer questions from my knowledge base
• Process documents you upload
• Have intelligent conversations
• Remember our chat history

**Commands:**
/help - Show this help
/stats - Your usage statistics
/clear - Clear conversation history

**Just send me a message to get started!** 🚀"""

        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """🤖 **How to use me:**

**Ask Questions:**
Just type your question naturally!
Example: "What is machine learning?"

**Upload Documents:**
Send me PDF or text files to add to my knowledge base.

**Commands:**
/start - Welcome message
/help - Show this help
/stats - Your usage statistics
/clear - Clear conversation history

**Tips:**
• I remember our conversation
• Upload docs for more context
• Ask follow-up questions

Try asking me something! 💬"""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user_id = str(update.effective_user.id)

        try:
            stats = self.rag_system.get_user_stats(user_id)

            stats_message = f"""📊 **Your Statistics**

• Documents: {stats.get('documents', 0)}
• Questions asked: {stats.get('queries', 0)}
• KB size: {stats.get('kb_size', 'N/A')}

Keep learning! 💪"""

            await update.message.reply_text(stats_message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"Error getting stats: {str(e)}")

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command"""
        user_id = str(update.effective_user.id)

        try:
            self.rag_system.clear_conversation(user_id)
            await update.message.reply_text("✅ Conversation history cleared! Starting fresh.")
        except Exception as e:
            await update.message.reply_text(f"Error clearing history: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        user_id = str(update.effective_user.id)
        message_text = update.message.text

        try:
            # Show typing indicator
            await update.message.chat.send_action("typing")

            # Get AI response
            response = self.rag_system.query_with_context(user_id, message_text)

            # Send response
            await update.message.reply_text(f"🤖 {response}")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error. Please try again."
            )

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads"""
        user_id = str(update.effective_user.id)
        document = update.message.document

        try:
            await update.message.reply_text("📄 Processing your document...")

            # Download file
            file = await document.get_file()
            suffix = Path(document.file_name or "upload").suffix or ".bin"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
                file_path = handle.name

            await file.download_to_drive(file_path)

            # Process document (you'll need to implement this)
            # For now, just acknowledge
            await update.message.reply_text(
                f"✅ Document '{document.file_name}' received!\n"
                f"Size: {document.file_size / 1024:.1f} KB\n\n"
                f"Processing documents is coming soon!"
            )

        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await update.message.reply_text(
                "Sorry, I couldn't process that document. Please try again."
            )
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.unlink(file_path)

    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Create and run bot
    bot = TelegramBot()
    bot.run()
