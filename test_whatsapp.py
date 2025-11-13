#!/usr/bin/env python3
"""
Test WhatsApp functionality locally
"""

import requests
import time

def test_whatsapp_webhook():
    """Test WhatsApp webhook locally"""
    
    base_url = "http://localhost:8000"
    
    # Test messages
    test_messages = [
        "hello",
        "help", 
        "stats",
        "What is artificial intelligence?",
        "Tell me about machine learning",
        "How does neural networks work?"
    ]
    
    print("🤖 Testing WhatsApp Bot Locally")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not running! Please start with: ./start.sh")
            return
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("Please start the server with: ./start.sh")
        return
    
    print("\n📱 Simulating WhatsApp Messages:")
    print("-" * 30)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. 📤 Sending: '{message}'")
        
        try:
            # Simulate WhatsApp webhook call
            response = requests.post(
                f"{base_url}/whatsapp/webhook",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "From": "whatsapp:+1234567890",
                    "Body": message
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse TwiML response
                response_text = response.text
                # Extract message content from TwiML
                if "<Message>" in response_text and "</Message>" in response_text:
                    start = response_text.find("<Message>") + 9
                    end = response_text.find("</Message>")
                    bot_response = response_text[start:end].strip()
                    print(f"📥 Bot Response: {bot_response}")
                else:
                    print(f"📥 Raw Response: {response_text}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Small delay between messages
        time.sleep(1)
    
    print(f"\n✅ WhatsApp test completed!")
    print("\n💡 To test with real WhatsApp:")
    print("1. Install ngrok: brew install ngrok")
    print("2. Run: ngrok http 8000")
    print("3. Set up Twilio WhatsApp sandbox")
    print("4. Configure webhook URL in Twilio")

if __name__ == "__main__":
    test_whatsapp_webhook()