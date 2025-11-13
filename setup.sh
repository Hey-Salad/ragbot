#!/bin/bash

echo "🚀 Setting up RAG Bot for Raspberry Pi..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p chroma_db uploads logs

# Copy environment file
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your actual credentials!"
fi

# Make scripts executable
chmod +x setup.sh
chmod +x start.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run: ./start.sh"
echo ""
echo "Your RAG bot will be available at:"
echo "- API: http://localhost:8000"
echo "- Health check: http://localhost:8000/health"
echo "- Upload docs: http://localhost:8000/upload"