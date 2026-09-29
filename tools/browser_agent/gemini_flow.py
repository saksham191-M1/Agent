import os
import sys
from colorama import Fore
from playwright.sync_api import sync_playwright

# Store the browser session here so you only log in to Google once
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_data")

def setup_login():
    """Opens a visible browser so the user can log into their Google account manually once."""
    print(f"{Fore.CYAN}Opening Browser Agent for Initial Login...{Fore.RESET}")
    print(f"{Fore.YELLOW}Please log into your Google Account. Close the browser window when you are fully logged in.{Fore.RESET}")
    
    with sync_playwright() as p:
        # Launch using a persistent context so cookies/login state are saved
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,  # Must be visible for manual login
        )
        page = browser.new_page()
        page.goto("https://gemini.google.com/")
        
        # Wait for the user to close the browser manually after logging in
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
            
        print(f"{Fore.GREEN}✅ Browser Session Saved! JARVIS now has access to Gemini Pro.{Fore.RESET}")

def generate_veo_media(prompt, output_filepath):
    """Secretly uses the saved session to generate a video/image."""
    print(f"{Fore.CYAN}🤖 Browser Agent: Navigating to Gemini...{Fore.RESET}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, # Keeping visible for now so we can watch it work
        )
        page = browser.new_page()
        page.goto("https://gemini.google.com/")
        
        print(f"{Fore.YELLOW}Waiting for chatbox...{Fore.RESET}")
        # Note: Google's DOM is highly dynamic. We will map the exact selectors to type the prompt
        # and extract the video in the next step.
        page.wait_for_timeout(5000) 
        
        print(f"{Fore.GREEN}Simulation complete for now.{Fore.RESET}")
        browser.close()

if __name__ == "__main__":
    setup_login()
