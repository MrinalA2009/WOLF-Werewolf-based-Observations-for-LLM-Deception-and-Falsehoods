#!/usr/bin/env python3
"""
Simple test script to verify Google API key works
"""

import os
import argparse
from langchain_google_genai import ChatGoogleGenerativeAI

def test_api_key(api_key=None, model="gemini-1.5-flash"):
    """Test if the Google API key works with a simple query"""
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    elif not os.environ.get("GOOGLE_API_KEY"):
        print("❌ No API key provided. Please set GOOGLE_API_KEY environment variable or use --api-key")
        return False
    
    try:
        print(f"🧪 Testing Google API key with model: {model}")
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=0.7
        )
        
        # Simple test query
        response = llm.invoke("Say 'Hello, Werewolf Game!' if you can respond.")
        print(f"✅ API Test Success! Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ API Test Failed: {str(e)}")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. API key doesn't have Generative AI access")
        print("3. Model name not supported")
        print("4. Network connectivity issues")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Google API key for Werewolf Game")
    parser.add_argument("--api-key", help="Google API key to test")
    parser.add_argument("--model", default="gemini-1.5-flash", help="Model to test with")
    
    args = parser.parse_args()
    
    success = test_api_key(args.api_key, args.model)
    exit(0 if success else 1)