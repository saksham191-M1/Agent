import os
import json
import urllib.parse
import requests
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, OUTPUT_DIR
from type1_ai.viral_ai import generate_audio, stitch_video
from colorama import Fore

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})

AD_PROMPT_TEMPLATE = """
Write a high-converting short-form video ad for the following product:
Product Name: "{product_name}"
Problem it Solves: "{problem}"
Call to Action (CTA): "{cta}"

You MUST use the PAS (Problem -> Agitate -> Solution -> CTA) copywriting framework.
The video must be fast-paced (under 30 seconds).

For each scene, provide:
1. "image_prompt": A highly detailed prompt for an AI image generator. Use styles like "commercial product photography, cinematic lighting, 8k resolution, highly detailed".
2. "voiceover": An energetic, persuasive Hindi/Hinglish voiceover.
3. "text_on_screen": The bold text that should flash on the screen to grab attention (e.g. "TIRED OF THIS?", "50% OFF TODAY").

Respond ONLY with a JSON object in this format:
{{
  "format": "ad",
  "scenes": [
    {{
      "scene": 1,
      "phase": "Problem",
      "image_prompt": "...",
      "voiceover": "...",
      "text_on_screen": "..."
    }}
  ]
}}
"""

def generate_ad_script(product_name, problem, cta):
    print(f"{Fore.CYAN}🧠 Writing PAS-framework Ad Script for '{product_name}'...{Fore.RESET}")
    prompt = AD_PROMPT_TEMPLATE.format(product_name=product_name, problem=problem, cta=cta)
    response = model.generate_content(prompt)
    try:
        data = json.loads(response.text)
        print(f"{Fore.GREEN}✅ Ad Script generated! (Scenes: {len(data['scenes'])}){Fore.RESET}")
        return data
    except Exception as e:
        print(f"{Fore.RED}Failed to parse ad script: {e}{Fore.RESET}")
        print("Raw response:", response.text)
        return None

def generate_ad_image(prompt, filepath):
    # Appending specific keywords to ensure high-quality ad visuals
    commercial_prompt = prompt + ", commercial product photography, depth of field, 8k, highly detailed"
    encoded_prompt = urllib.parse.quote(commercial_prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
    else:
        print(f"{Fore.RED}Failed to fetch ad image.{Fore.RESET}")

def run_type1_ad_pipeline():
    print(f"\n{Fore.MAGENTA}=== AI PRODUCT AD INTAKE ==={Fore.RESET}")
    product_name = input("1. What is the Product Name?: ")
    problem = input("2. What problem does it solve? (e.g. 'Back pain', 'Boring car interiors'): ")
    cta = input("3. What is the Call to Action? (e.g. 'Click link in bio for 50% off'): ")
    
    script_data = generate_ad_script(product_name, problem, cta)
    if not script_data:
        return
        
    scenes = script_data.get('scenes', [])
    scenes_data = []
    
    for i, scene in enumerate(scenes):
        print(f"\n{Fore.CYAN}--- {scene.get('phase', 'Scene').upper()} ---{Fore.RESET}")
        
        voiceover = scene.get('voiceover', '').strip()
        text_on_screen = scene.get('text_on_screen', '')
        
        print(f"Text Overlay: [ {text_on_screen} ]")
        print(f"Voiceover: {voiceover}")
        
        audio_path = os.path.join(OUTPUT_DIR, "audio", f"ad_scene_{i}.mp3")
        image_path = os.path.join(OUTPUT_DIR, "thumbnails", f"ad_scene_{i}.jpg")
        
        print(f"🎙️ Generating enthusiastic voiceover...")
        # Using a very energetic/sales-oriented voice pitch if possible, standard for now
        generate_audio(voiceover, audio_path, voice="hi-IN-MadhurNeural")
        
        print(f"📸 Generating commercial product image...")
        generate_ad_image(scene['image_prompt'], image_path)
        
        scenes_data.append({
            "audio_path": audio_path,
            "image_path": image_path,
            "text": text_on_screen
        })
        
    output_video = os.path.join(OUTPUT_DIR, "videos", f"AD_{product_name.replace(' ', '_')}.mp4")
    stitch_video(scenes_data, output_video, format_type="ad")
