#!/usr/bin/env python3
"""
Simple test script for WhatsApp webhook functionality
"""

import requests

def test_whatsapp_webhook():
    """Test WhatsApp webhook locally"""
    url = "http://localhost:8000/whatsapp/webhook"
    
    # Test data simulating Twilio webhook
    test_data = {
        "From": "whatsapp:+1234567890",
        "Body": "What is artificial intelligence?"
    }
    
    print("🧪 Testing WhatsApp webhook...")
    print(f"URL: {url}")
    print(f"Test message: {test_data['Body']}")
    
    try:
        response = requests.post(
            url,
            data=test_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ WhatsApp webhook test passed!")
        else:
            print("❌ WhatsApp webhook test failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_whatsapp_webhook()