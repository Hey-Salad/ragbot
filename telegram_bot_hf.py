#!/usr/bin/env python3
"""
Simple Telegram Bot using YOUR working Hugging Face setup
Based on your tested /home/admin/simple_usage.py
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from huggingface_hub import InferenceClient

# Load environment
from dotenv import load_dotenv
load_dotenv('.env.telegram')

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Hugging Face client (exactly like your simple_usage.py)
HF_TOKEN = os.getenv('HUGGINGFACE_HUB_TOKEN', 'YOUR_HF_TOKEN_HERE')
MODEL = os.getenv('HF_MODEL', 'openai/gpt-oss-120b')

client = InferenceClient(token=HF_TOKEN)

logger.info(f"✅ Initialized Hugging Face client with model: {MODEL}")


def get_ai_response(message: str) -> str:
    """Get AI response using your working HF setup"""
    try:
        # Use InferenceClient exactly like your simple_usage.py
        response = client.chat_completion(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": message
            }],
            max_tokens=500,
            temperature=0.7
        )

        # Extract response text
        if response and response.choices:
            return response.choices[0].message.content

        return "Sorry, I didn't get a response from the AI."

    except Exception as e:
        logger.error(f"AI Error: {e}")
        return f"Error: {str(e)}"


# Telegram command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hi {user.first_name}!\n\n"
        f"I'm powered by Hugging Face GPT-OSS-120B.\n\n"
        f"Just send me a message and I'll respond!\n\n"
        f"Commands:\n"
        f"/start - This message\n"
        f"/help - Show help\n"
        f"/model - Show current model"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help"""
    await update.message.reply_text(
        "🤖 **How to use:**\n\n"
        "Just type your question or message!\n\n"
        "Examples:\n"
        "• What is 2+2?\n"
        "• Explain quantum computing\n"
        "• Tell me a joke\n\n"
        "I'm using Hugging Face GPT-OSS-120B 🚀"
    )


async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current model info"""
    await update.message.reply_text(
        f"📊 **Current Model:**\n\n"
        f"Model: {MODEL}\n"
        f"Provider: Hugging Face\n"
        f"Token: {HF_TOKEN[:15]}...\n"
        f"Status: ✅ Active"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    user = update.effective_user
    message_text = update.message.text

    logger.info(f"Message from {user.first_name}: {message_text[:50]}...")

    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")

        # Get AI response using your working code
        response = get_ai_response(message_text)

        # Send response
        await update.message.reply_text(f"🤖 {response}")

        logger.info(f"Response sent successfully")

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error. Please try again."
        )


def main():
    """Run the bot"""
    # Get token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env.telegram")
        return

    # Create application
    print(f"🚀 Starting Telegram bot...")
    print(f"📡 Model: {MODEL}")
    print(f"🔑 HF Token: {HF_TOKEN[:20]}...")

    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("model", model_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run bot
    print("✅ Bot is running! Send a message to @heysalad_ai_bot")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
