#!/bin/bash

echo "🤖 Starting RAG Bot..."

# Activate virtual environment
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
elif [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found! Please run ./setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found! Please copy .env.example to .env and configure it."
    exit 1
fi

# Start the application
echo "🚀 Launching RAG Bot API..."
python3 main.py
