#!/usr/bin/env python3
"""
Test script for RAG Bot API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("\n📊 Testing stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def test_query():
    """Test query endpoint"""
    print("\n🤖 Testing query endpoint...")
    try:
        test_question = "What is artificial intelligence?"
        payload = {"question": test_question}
        
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Question: {test_question}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Answer: {result.get('answer', 'No answer')}")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def test_upload():
    """Test upload endpoint with sample text"""
    print("\n📄 Testing upload endpoint...")
    try:
        # Create a sample text file
        sample_text = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines that work and react like humans. Some of the activities 
        computers with artificial intelligence are designed for include:
        
        - Speech recognition
        - Learning
        - Planning
        - Problem solving
        
        Machine Learning is a subset of AI that provides systems the ability to 
        automatically learn and improve from experience without being explicitly programmed.
        """
        
        files = {
            'file': ('sample_doc.txt', sample_text, 'text/plain')
        }
        
        response = requests.post(f"{BASE_URL}/upload", files=files)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload result: {result}")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting RAG Bot API Tests")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Stats", test_stats),
        ("Upload Document", test_upload),
        ("Query System", test_query),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        success = test_func()
        results.append((test_name, success))
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG Bot is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs and configuration.")

if __name__ == "__main__":
    main()