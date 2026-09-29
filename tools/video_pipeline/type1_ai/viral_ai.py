import os
import json
import urllib.parse
import requests
import google.generativeai as genai
from config.settings import GEMINI_API_KEY, OUTPUT_DIR
import edge_tts
import asyncio
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from colorama import Fore

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash', generation_config={"response_mime_type": "application/json"})

PROMPT_TEMPLATE = """
Write a short viral video script about: "{keyword}".
The video should be 3-4 scenes (under 30 seconds total).
For each scene, provide:
1. "image_prompt": A highly detailed prompt for an AI image generator (e.g. "cinematic lighting, 4k, hyperrealistic, [subject]").
2. "voiceover": The Hindi/Hinglish narration for this scene.

Respond ONLY with a JSON array in this format:
[
  {
    "scene": 1,
    "image_prompt": "...",
    "voiceover": "..."
  }
]
"""

def generate_script(keyword):
    print(f"{Fore.CYAN}🧠 Asking Gemini to write the script for '{keyword}'...{Fore.RESET}")
    response = model.generate_content(PROMPT_TEMPLATE.format(keyword=keyword))
    try:
        scenes = json.loads(response.text)
        print(f"{Fore.GREEN}✅ Script generated with {len(scenes)} scenes.{Fore.RESET}")
        return scenes
    except Exception as e:
        print(f"{Fore.RED}Failed to parse script: {e}{Fore.RESET}")
        print("Raw response:", response.text)
        return []

async def generate_audio_async(text, filepath):
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural")
    await communicate.save(filepath)

def generate_audio(text, filepath):
    asyncio.run(generate_audio_async(text, filepath))

def generate_image(prompt, filepath):
    # Using Pollinations.ai for instant free AI image generation
    # Later we will swap this to your local SDXL on the RTX 3050
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
    else:
        print(f"{Fore.RED}Failed to fetch image.{Fore.RESET}")

def stitch_video(scenes_data, output_filename):
    print(f"{Fore.YELLOW}🎬 Stitching video together...{Fore.RESET}")
    clips = []
    
    for data in scenes_data:
        audio_path = data['audio_path']
        image_path = data['image_path']
        
        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        
        # Create image clip matching audio duration
        image_clip = ImageClip(image_path).set_duration(duration)
        image_clip = image_clip.set_audio(audio_clip)
        
        clips.append(image_clip)
        
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", logger=None)
    print(f"{Fore.GREEN}🎉 Video saved to {output_filename}{Fore.RESET}")

def run_type1_viral_pipeline(keyword):
    scenes = generate_script(keyword)
    if not scenes:
        return
        
    scenes_data = []
    
    for i, scene in enumerate(scenes):
        print(f"\n{Fore.CYAN}--- Processing Scene {i+1} ---{Fore.RESET}")
        print(f"Voiceover: {scene['voiceover']}")
        
        audio_path = os.path.join(OUTPUT_DIR, "audio", f"scene_{i}.mp3")
        image_path = os.path.join(OUTPUT_DIR, "thumbnails", f"scene_{i}.jpg")
        
        print(f"🎙️ Generating voiceover...")
        generate_audio(scene['voiceover'], audio_path)
        
        print(f"🎨 Generating AI image (Pollinations API)...")
        generate_image(scene['image_prompt'], image_path)
        
        scenes_data.append({
            "audio_path": audio_path,
            "image_path": image_path
        })
        
    output_video = os.path.join(OUTPUT_DIR, "videos", f"viral_{keyword.replace(' ', '_')}.mp4")
    stitch_video(scenes_data, output_video)
