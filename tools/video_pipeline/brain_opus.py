import os
import sys
import json
import requests
from dotenv import load_dotenv
from colorama import Fore, init

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))
init(autoreset=True)

def generate_multi_scene_blueprint(product_name):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"{Fore.RED}Error: GEMINI_API_KEY missing from .env{Fore.RESET}")
        sys.exit(1)
        
    prompt = f"""
    You are an Opus-level Creative Director building an automated video pipeline for a product called '{product_name}'.
    The user wants a highly persuasive 'Problem-Agitate-Solution' (PAS) business ad to gain trust.
    You must autonomously break this down into exactly 4 distinct video scenes.
    Scenes 2 and 3 MUST focus on showcasing the actual app UI workflow to build trust.
    
    Output a JSON object with this exact structure:
    {{
        "product_name": "{product_name}",
        "selected_template": "Problem-Agitate-Solution (UI Showcase)",
        "scenes": [
            {{
                "scene_id": 1,
                "duration_seconds": 4,
                "voiceover": "State the painful problem clearly.",
                "veo_prompt": "Prompt for Veo to generate a cinematic stock video of the problem.",
                "visual_fx": "fast_zoom",
                "kinetic_text": "The main bold word (e.g. BROKEN)",
                "requires_ui_image": false
            }},
            {{
                "scene_id": 2,
                "duration_seconds": 5,
                "voiceover": "Introduce the product as the solution.",
                "veo_prompt": "Prompt for Veo to take the uploaded UI image and map it onto a 3D floating glass card. Slow camera push-in.",
                "visual_fx": "glass_ui",
                "kinetic_text": "The solution word",
                "requires_ui_image": true
            }}
            // Scene 3 (Deep dive UI workflow, requires_ui_image: true)
            // Scene 4 (CTA/Logo, requires_ui_image: false)
        ]
    }}
    Ensure valid JSON only. Do not use markdown blocks like ```json.
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"{Fore.RED}API Error: {response.status_code} - {response.text}{Fore.RESET}")
        sys.exit(1)
        
    response_json = response.json()
    return response_json['candidates'][0]['content']['parts'][0]['text']

if __name__ == "__main__":
    app = sys.argv[1] if len(sys.argv) > 1 else "Swiggy"
    print(f"{Fore.CYAN}=== OPUS DIRECTOR AI: AUTONOMOUS STORYBOARD FOR '{app.upper()}' ==={Fore.RESET}\n")
    
    try:
        raw_result = generate_multi_scene_blueprint(app)
        cleaned_json = raw_result.replace('```json', '').replace('```', '').strip()
        data = json.loads(cleaned_json)
        
        print(f"{Fore.MAGENTA}Chosen Template: {data['selected_template']}{Fore.RESET}\n")
        
        for scene in data['scenes']:
            print(f"{Fore.YELLOW}🎬 SCENE {scene['scene_id']} ({scene['duration_seconds']}s){Fore.RESET}")
            print(f"   {Fore.CYAN}Veo Prompt:{Fore.RESET} {scene['veo_prompt']}")
            print(f"   {Fore.GREEN}Voiceover:{Fore.RESET}  {scene['voiceover']}")
            print(f"   {Fore.WHITE}Visual FX:{Fore.RESET}  {scene['visual_fx']}")
            print(f"   {Fore.WHITE}Text Overlay:{Fore.RESET} {scene['kinetic_text']}\n")
            
        print(f"{Fore.GREEN}✅ The AI Brain successfully made all creative decisions autonomously.{Fore.RESET}")
        
    except Exception as e:
        print(f"{Fore.RED}Error during dry run: {e}{Fore.RESET}")
