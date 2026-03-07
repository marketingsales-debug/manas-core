import os
import json
import requests
from pathlib import Path

# Load config
config_path = Path("/Users/avipattan/manas/config/llm_config.json")
with open(config_path, "r") as f:
    config = json.load(f)

print("Starting API tests...")

# 1. Test Groq
print("\n--- Testing Groq ---")
try:
    groq_key = config["default_cloud"].get("api_key")
    if not groq_key:
        print("Groq API key missing in config.")
    else:
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "Say 'Groq works'."}],
            "max_tokens": 10
        }
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        if res.status_code == 200:
            print("Groq SUCCESS:", res.json()["choices"][0]["message"]["content"])
        else:
            print(f"Groq FAILED: {res.status_code} - {res.text}")
except Exception as e:
    print("Groq ERROR:", e)

# 2. Test Anthropic
print("\n--- Testing Anthropic ---")
try:
    anth_key = config["complex_coding"].get("api_key")
    if not anth_key:
        print("Anthropic API key missing in config.")
    else:
        headers = {
            "x-api-key": anth_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Say 'Anthropic works'."}]
        }
        res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        if res.status_code == 200:
            print("Anthropic SUCCESS:", res.json()["content"][0]["text"])
        else:
            print(f"Anthropic FAILED: {res.status_code} - {res.text}")
except Exception as e:
    print("Anthropic ERROR:", e)

# 3. Test Gemini
print("\n--- Testing Gemini ---")
try:
    gemini_key = config["vision"].get("api_key")
    if not gemini_key:
        print("Gemini API key missing in config.")
    else:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "contents": [{"parts":[{"text": "Say 'Gemini works'."}]}]
        }
        # Use gemini-2.0-flash as it was confirmed in ListModels
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}", 
            headers=headers, 
            json=data
        )
        if res.status_code == 200:
            print("Gemini SUCCESS:", res.json()["candidates"][0]["content"]["parts"][0]["text"].strip())
        else:
            print(f"Gemini FAILED: {res.status_code} - {res.text}")
except Exception as e:
    print("Gemini ERROR:", e)

# 4. Test Mistral
print("\n--- Testing Mistral ---")
try:
    mistral_key = config.get("default_mistral", {}).get("api_key")
    if not mistral_key:
        print("Mistral API key missing in config.")
    else:
        from mistralai import Mistral
        client = Mistral(api_key=mistral_key)
        res = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": "Say 'Mistral works'."}],
            max_tokens=10
        )
        print("Mistral SUCCESS:", res.choices[0].message.content)
except Exception as e:
    print(f"Mistral FAILED: {e}")

# 5. Test Claude CLI (Bonsai related)
print("\n--- Testing Claude CLI ---")
import subprocess
try:
    # Use -p flag for simple prompt
    result = subprocess.run(["claude", "-p", "Say 'Claude CLI works' and exit"], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        print("Claude CLI SUCCESS:", result.stdout.strip())
    else:
        # Check if it's just a warning about interactive mode
        print(f"Claude CLI Result: {result.returncode}")
        print(f"STDOUT: {result.stdout[:200]}...")
except Exception as e:
    print(f"Claude CLI ERROR: {e}")

print("\nTests complete.")
