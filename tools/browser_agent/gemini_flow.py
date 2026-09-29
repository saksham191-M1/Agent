import os
import sys
from colorama import Fore
from playwright.sync_api import sync_playwright

from config.settings import os
from dotenv import load_dotenv

# Make sure we load the latest .env vars
load_dotenv()

# Store the browser session here
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_data")

def inject_cookies_and_verify(page):
    """Injects the Gemini cookie and verifies login."""
    cookie_value = os.getenv("GEMINI_COOKIE")
    if not cookie_value:
        print(f"{Fore.RED}❌ Error: GEMINI_COOKIE not found in .env file!{Fore.RESET}")
        return False
        
    print(f"{Fore.CYAN}Injecting Session Cookie...{Fore.RESET}")
    page.context.add_cookies([{
        "name": "__Secure-1PSID",
        "value": cookie_value,
        "domain": ".google.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
        "sameSite": "Lax"
    }])
    
    page.goto("https://gemini.google.com/")
    page.wait_for_timeout(3000)
    
    # Check if we successfully bypassed login
    if "Sign in" in page.title() or "Sign in" in page.content():
        print(f"{Fore.RED}❌ Cookie injection failed or cookie is expired. Please get a fresh __Secure-1PSID cookie.{Fore.RESET}")
        return False
        
    print(f"{Fore.GREEN}✅ Cookie Injection Successful! JARVIS is securely logged in.{Fore.RESET}")
    return True

def setup_login():
    """Verifies the cookie works by opening a visible browser."""
    print(f"{Fore.CYAN}Testing Browser Agent Cookie Authentication...{Fore.RESET}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
        )
        page = browser.new_page()
        
        success = inject_cookies_and_verify(page)
        
        if success:
            print(f"{Fore.YELLOW}Closing browser in 5 seconds...{Fore.RESET}")
            page.wait_for_timeout(5000)
            
def generate_veo_media(prompt, output_filepath):
    """Secretly uses the saved session to generate a video/image."""
    print(f"{Fore.CYAN}🤖 Browser Agent: Navigating to Gemini...{Fore.RESET}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, # Keeping visible for now so we can watch it work
        )
        page = browser.new_page()
        
        if not inject_cookies_and_verify(page):
            return False
            
        print(f"{Fore.YELLOW}Waiting for chatbox...{Fore.RESET}")
        # Note: Google's DOM is highly dynamic. We will map the exact selectors to type the prompt
        # and extract the video in the next step.
        page.wait_for_timeout(5000) 
        
        print(f"{Fore.GREEN}Simulation complete for now.{Fore.RESET}")
        browser.close()

if __name__ == "__main__":
    setup_login()
