import os
import sys
import threading
from config.logger import logger
from security.auth_window import AuthWindow

def start_jarvis():
    logger.info("Authentication successful. Starting JARVIS...")
    
    # We import ui here so that Gradio and Gemini only load AFTER auth is successful
    from ui.chat_app import launch_ui
    from voice.output_engine import speak
    
    # Speak a welcome message in background
    threading.Thread(target=speak, args=("Authentication successful. Welcome back.",), daemon=True).start()
    
    # Launch UI
    launch_ui()

if __name__ == "__main__":
    logger.info("Initializing JARVIS Security Protocol...")
    # Show auth window first
    auth_win = AuthWindow(on_success=start_jarvis)
    auth_win.run()
