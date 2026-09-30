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
            
def generate_veo_media(prompt, output_filepath, image_path=None):
    """Secretly uses the saved session to type a prompt (and upload an image), wait for Veo video, and download it."""
    print(f"{Fore.CYAN}🌐 Browser Agent: Infiltrating Gemini Web...{Fore.RESET}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False, 
            accept_downloads=True
        )
        page = browser.new_page()
        
        if not inject_cookies_and_verify(page):
            return False
            
        print(f"{Fore.YELLOW}✍️ Locating chat interface...{Fore.RESET}")
        chatbox = page.locator('rich-textarea, textarea, [contenteditable="true"]').first
        chatbox.wait_for(state="visible", timeout=15000)
        
        # Image Upload Logic
        if image_path and os.path.exists(image_path):
            print(f"{Fore.MAGENTA}🖼️ Uploading UI Screenshot: {os.path.basename(image_path)}{Fore.RESET}")
            # Gemini has a hidden file input we can target
            file_input = page.locator('input[type="file"]').first
            file_input.set_input_files(image_path)
            # Wait a second for the image to attach to the chatbox
            page.wait_for_timeout(3000)
        
        chatbox.click()
        full_prompt = f"Generate a high quality video using Veo based on this image: {prompt}"
        page.keyboard.type(full_prompt)
        page.wait_for_timeout(1000)
        page.keyboard.press("Enter")
        
        print(f"{Fore.YELLOW}⏳ Prompt submitted. Waiting for Veo to generate the video (this can take 1-3 minutes)...{Fore.RESET}")
        
        try:
            page.wait_for_selector('video', timeout=180000)
            print(f"{Fore.GREEN}🎥 Video generation complete! Found video element.{Fore.RESET}")
            page.wait_for_timeout(3000)
            
            video_src = page.evaluate('''() => {
                const vid = document.querySelector('video');
                return vid ? vid.src : null;
            }''')
            
            if video_src:
                if video_src.startswith('blob:'):
                    print(f"{Fore.CYAN}📥 Intercepting Blob Video stream and saving to disk...{Fore.RESET}")
                    base64_vid = page.evaluate('''async (blobUrl) => {
                        const response = await fetch(blobUrl);
                        const blob = await response.blob();
                        return new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        });
                    }''', video_src)
                    
                    import base64
                    b64_data = base64_vid.split(',')[1]
                    with open(output_filepath, "wb") as f:
                        f.write(base64.b64decode(b64_data))
                    print(f"{Fore.GREEN}✅ Video successfully saved to {output_filepath}{Fore.RESET}")
                else:
                    print(f"{Fore.YELLOW}Warning: Non-blob video source found. Needs direct download handling.{Fore.RESET}")
            else:
                print(f"{Fore.RED}❌ Could not extract video source.{Fore.RESET}")
                
        except Exception as e:
            print(f"{Fore.RED}❌ Timeout or Error waiting for Veo video: {e}{Fore.RESET}")
        
        page.wait_for_timeout(2000)
        browser.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, help="The Veo prompt to generate")
    parser.add_argument("--out", type=str, default="test_veo.mp4", help="Output filename")
    parser.add_argument("--image", type=str, help="Path to UI screenshot for Image-to-Video")
    args = parser.parse_args()
    
    if args.prompt:
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "raw_videos", args.out)
        generate_veo_media(args.prompt, out_path, image_path=args.image)
    else:
        setup_login()
