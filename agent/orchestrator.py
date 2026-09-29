import google.generativeai as genai
from config.settings import GEMINI_API_KEY
from agent.memory import get_conversation_history, add_message, clear_history
import logging

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
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            logger.error("GEMINI_API_KEY is not set correctly in .env!")
            self.model = None
        else:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
            logger.info("Gemini model configured.")

    def process_message(self, user_text):
        if not self.model:
            return "API Key set nahi hai bhai! .env file check karo."
            
        if user_text.lower().strip() in ["clear", "reset", "bhul jao"]:
            clear_history()
            return "Sab kuch bhula diya! New session started. 🔄"
        
        # Save user message
        add_message('user', user_text)
        
        # Build history format for Gemini
        raw_history = get_conversation_history(limit=20)
        history = []
        # Exclude the message we just added to pass it as the current message
        for msg in raw_history[:-1]: 
            role = 'model' if msg['role'] == 'assistant' else 'user'
            history.append({"role": role, "parts": [msg['content']]})
        
        try:
            chat = self.model.start_chat(history=history)
            response = chat.send_message(user_text)
            reply = response.text
            
            # Save assistant message
            add_message('assistant', reply)
            return reply
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "Arre yaar, koi network issue lag raha hai ya API limit aa gayi."
