import os
import json
import urllib.parse
import requests
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, OUTPUT_DIR
from type1_ai.viral_ai import generate_audio, stitch_video
from colorama import Fore
from PIL import Image, ImageDraw

def create_placeholder(filepath):
    img = Image.new('RGB', (1080, 1920), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((100, 960), "Image Gen Failed - Placeholder", fill=(255, 255, 0))
    img.save(filepath)

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
    # The correct API endpoint for the raw image is image.pollinations.ai
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    try:
        response = requests.get(url, timeout=30)
        # Check if the response is an actual image, not an HTML error page
        if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
            with open(filepath, 'wb') as f:
                f.write(response.content)
        else:
            print(f"{Fore.RED}Failed to fetch ad image (Invalid response). Creating placeholder.{Fore.RESET}")
            create_placeholder(filepath)
    except Exception as e:
        print(f"{Fore.RED}Error fetching image: {e}. Creating placeholder.{Fore.RESET}")
        create_placeholder(filepath)

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
