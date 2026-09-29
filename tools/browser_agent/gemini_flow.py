import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from colorama import Fore
from playwright.sync_api import sync_playwright

# Add jarvis root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import os
from dotenv import load_dotenv

# Make sure we load the latest .env vars
load_dotenv()

# Store the browser session here
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_data")

def inject_cookies_and_verify(page):
    """Injects the Gemini cookies and verifies login."""
    cookie_psid = os.getenv("GEMINI_COOKIE")
    cookie_ts = os.getenv("GEMINI_COOKIE_TS")
    cookie_cc = os.getenv("GEMINI_COOKIE_CC")
    
    if not cookie_psid:
        print(f"{Fore.RED}❌ Error: GEMINI_COOKIE not found in .env file!{Fore.RESET}")
        return False
        
    print(f"{Fore.CYAN}Injecting Session Cookies...{Fore.RESET}")
    
    cookies = []
    base_cookie = {
        "domain": ".google.com",
        "path": "/",
        "secure": True,
        "httpOnly": True,
        "sameSite": "Lax"
    }
    
    cookies.append({"name": "__Secure-1PSID", "value": cookie_psid, **base_cookie})
    if cookie_ts:
        cookies.append({"name": "__Secure-1PSIDTS", "value": cookie_ts, **base_cookie})
    if cookie_cc:
        cookies.append({"name": "__Secure-1PSIDCC", "value": cookie_cc, **base_cookie})
        
    page.context.add_cookies(cookies)
    
    page.goto("https://gemini.google.com/")
    page.wait_for_timeout(5000)
    
    # Check if the title is strictly asking to sign in
    title = page.title().lower()
    if title == "sign in - google accounts" or title == "google login":
        print(f"{Fore.RED}❌ Cookie injection failed. Google rejected the session.{Fore.RESET}")
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
