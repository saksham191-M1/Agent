import os
import sys
import requests
import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from agent.memory import get_conversation_history, add_message, clear_history
import logging

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

logger = logging.getLogger("JARVIS")

# System Prompt
SYSTEM_PROMPT = """You are JARVIS, a personal AI assistant.
- Speak in friendly Hinglish (Hindi + English mix) written in Latin/English script.
- Keep responses conversational, concise, and smart.
- When asked to do a task, acknowledge it and say what you're doing.
- Be enthusiastic. Use emojis naturally.
"""

class Orchestrator:
    def __init__(self):
        self.codecraft_key = os.getenv("CODECRAFT_API_KEY")
        self.codecraft_model = os.getenv("CODECRAFT_MODEL", "claude-opus-5.5")
        self.codecraft_base = os.getenv("CODECRAFT_BASE_URL", "https://codecraftapi.com/v1").rstrip("/")
        
        self.gemini_model = None
        if self.codecraft_key:
            logger.info(f"CodeCraft API configured with {self.codecraft_model}.")
        elif GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-3.5-flash', system_instruction=SYSTEM_PROMPT)
                logger.info("Gemini model configured.")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")
        else:
            logger.error("Neither CODECRAFT_API_KEY nor GEMINI_API_KEY is configured!")

    def process_message(self, user_text):
        if not self.codecraft_key and not self.gemini_model:
            return "API Key set nahi hai bhai! .env file check karo."
            
        if user_text.lower().strip() in ["clear", "reset", "bhul jao"]:
            clear_history()
            return "Sab kuch bhula diya! New session started. 🔄"
        
        # Save user message
        add_message('user', user_text)
        raw_history = get_conversation_history(limit=20)
        
        # 1. Primary: CodeCraft API (Claude Opus 5.5 / Sonnet)
        if self.codecraft_key:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for msg in raw_history:
                messages.append({"role": msg['role'], "content": msg['content']})
            try:
                headers = {
                    "Authorization": f"Bearer {self.codecraft_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.codecraft_model,
                    "messages": messages,
                    "temperature": 0.7
                }
                res = requests.post(f"{self.codecraft_base}/chat/completions", headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    reply = res.json()["choices"][0]["message"]["content"]
                    add_message('assistant', reply)
                    return reply
                else:
                    logger.warning(f"CodeCraft API returned {res.status_code}: {res.text[:200]}")
            except Exception as e:
                logger.error(f"Error calling CodeCraft API: {e}")
                
        # 2. Secondary Fallback: Gemini
        if self.gemini_model:
            history = []
            for msg in raw_history[:-1]: 
                role = 'model' if msg['role'] == 'assistant' else 'user'
                history.append({"role": role, "parts": [msg['content']]})
            try:
                chat = self.gemini_model.start_chat(history=history)
                response = chat.send_message(user_text)
                reply = response.text
                add_message('assistant', reply)
                return reply
            except Exception as e:
                logger.error(f"Error calling Gemini: {e}")
                
        return "Arre yaar, koi network issue lag raha hai ya API limit aa gayi."
