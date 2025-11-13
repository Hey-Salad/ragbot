#!/usr/bin/env python3
"""
Simple test to check FlexaAI playground endpoint
"""

import requests
import json
from config import Config

def test_playground_endpoint():
    config = Config()
    
    # The URL you provided seems to be a playground URL
    # Let's try to find the actual API endpoint
    
    print("🔍 Testing FlexaAI Playground...")
    print(f"URL: {config.FLEXAI_API_URL}")
    
    # Try different approaches
    headers = {
        "Authorization": f"Bearer {config.FLEXAI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Test if there's an API endpoint
    api_endpoints = [
        "",  # Base URL
        "/api",
        "/api/v1",
        "/api/generate", 
        "/api/chat",
        "/inference",
        "/predict"
    ]
    
    for endpoint in api_endpoints:
        url = f"{config.FLEXAI_API_URL}{endpoint}"
        
        print(f"\n📡 Testing: {url}")
        
        # Try GET first
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f"GET Status: {response.status_code}")
            if response.status_code != 404:
                print(f"GET Response: {response.text[:200]}...")
        except Exception as e:
            print(f"GET Error: {str(e)}")
        
        # Try POST with simple payload
        try:
            payload = {"prompt": "Hello", "max_tokens": 10}
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            print(f"POST Status: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ SUCCESS! POST Response: {response.text}")
                return url, payload
            elif response.status_code != 404 and response.status_code != 405:
                print(f"POST Response: {response.text[:200]}...")
        except Exception as e:
            print(f"POST Error: {str(e)}")
    
    print("\n💡 The URL appears to be a web playground interface.")
    print("You might need to:")
    print("1. Check FlexaAI documentation for the correct API endpoint")
    print("2. Look for an 'API' or 'Developer' section in the FlexaAI dashboard")
    print("3. The playground URL might have a different API endpoint")
    
    return None, None

if __name__ == "__main__":
    test_playground_endpoint()