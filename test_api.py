#!/usr/bin/env python3
"""
Simple test script to verify API key works (OpenAI or Google)
"""

import os
import argparse
from dotenv import load_dotenv


def test_google(api_key=None, model="gemini-1.5-flash") -> bool:
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as e:
        print(f"❌ Google provider not available: {e}")
        return False

    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    elif not os.environ.get("GOOGLE_API_KEY"):
        print("❌ No Google API key provided. Set GOOGLE_API_KEY or use --api-key")
        return False

    try:
        print(f"🧪 Testing Google API key with model: {model}")
        llm = ChatGoogleGenerativeAI(model=model, temperature=0.2)
        response = llm.invoke("ping").content
        print(f"✅ Google API Test Success! Response: {response[:80]}...")
        return True
    except Exception as e:
        print(f"❌ Google API Test Failed: {str(e)}")
        return False


def test_openai(api_key=None, model="gpt-4o-mini") -> bool:
    try:
        from langchain_openai import ChatOpenAI
    except Exception as e:
        print(f"❌ OpenAI provider not available: {e}")
        return False

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    elif not os.environ.get("OPENAI_API_KEY"):
        print("❌ No OpenAI API key provided. Set OPENAI_API_KEY or use --api-key")
        return False

    try:
        print(f"🧪 Testing OpenAI API key with model: {model}")
        llm = ChatOpenAI(model=model, temperature=0.2)
        response = llm.invoke("ping").content
        print(f"✅ OpenAI API Test Success! Response: {response[:80]}...")
        return True
    except Exception as e:
        print(f"❌ OpenAI API Test Failed: {str(e)}")
        return False


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser(description="Test API key for Werewolf Game")
    parser.add_argument("--api-key", help="API key to test (overrides environment)")
    parser.add_argument("--provider", choices=["auto", "openai", "google"], default="auto")
    parser.add_argument("--model", default=None, help="Model to test with (optional)")

    args = parser.parse_args()

    # Provider selection
    provider = args.provider
    success = False

    if provider == "openai" or (provider == "auto" and (args.api_key or os.getenv("OPENAI_API_KEY"))):
        model = args.model or "gpt-4o-mini"
        success = test_openai(args.api_key, model)
    elif provider == "google" or (provider == "auto" and (args.api_key or os.getenv("GOOGLE_API_KEY"))):
        model = args.model or "gemini-1.5-flash"
        success = test_google(args.api_key, model)
    else:
        # Auto and no key: try OpenAI then Google so both env names are supported
        if os.getenv("OPENAI_API_KEY"):
            success = test_openai(None, args.model or "gpt-4o-mini")
        elif os.getenv("GOOGLE_API_KEY"):
            success = test_google(None, args.model or "gemini-1.5-flash")
        else:
            print("❌ No API key provided. Set OPENAI_API_KEY or GOOGLE_API_KEY, or pass --api-key.")
            success = False

    exit(0 if success else 1)