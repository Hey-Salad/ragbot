#!/usr/bin/env python3
"""
Test script to figure out the correct FlexaAI API format
"""

import requests
import json
from config import Config

def test_flexai_endpoints():
    config = Config()
    
    headers = {
        "Authorization": f"Bearer {config.FLEXAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_prompt = "What is artificial intelligence?"
    
    # Test different endpoint formats
    endpoints_to_try = [
        "/v1/chat/completions",
        "/v1/completions", 
        "/chat/completions",
        "/completions",
        "/generate",
        "/v1/generate"
    ]
    
    # Test different payload formats
    payloads_to_try = [
        {
            "messages": [{"role": "user", "content": test_prompt}],
            "max_tokens": 100,
            "temperature": 0.7
        },
        {
            "prompt": test_prompt,
            "max_tokens": 100,
            "temperature": 0.7
        },
        {
            "input": test_prompt,
            "max_tokens": 100,
            "temperature": 0.7
        },
        {
            "text": test_prompt,
            "max_tokens": 100
        }
    ]
    
    print("🔍 Testing FlexaAI API endpoints...")
    print(f"Base URL: {config.FLEXAI_API_URL}")
    print("=" * 60)
    
    for endpoint in endpoints_to_try:
        for i, payload in enumerate(payloads_to_try):
            url = f"{config.FLEXAI_API_URL}{endpoint}"
            
            try:
                print(f"\n📡 Testing: {endpoint} with payload format {i+1}")
                print(f"URL: {url}")
                print(f"Payload: {json.dumps(payload, indent=2)}")
                
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ SUCCESS!")
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    return endpoint, payload  # Return successful combination
                else:
                    print(f"❌ Error: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Exception: {str(e)}")
    
    print("\n🤔 None of the standard endpoints worked. Let's try a simple GET request to see what's available:")
    
    # Try GET request to see available endpoints
    try:
        response = requests.get(config.FLEXAI_API_URL, headers=headers, timeout=10)
        print(f"GET Status: {response.status_code}")
        print(f"GET Response: {response.text}")
    except Exception as e:
        print(f"GET Exception: {str(e)}")
    
    return None, None

if __name__ == "__main__":
    test_flexai_endpoints()