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
Write a short viral short-form video script about: "{keyword}".
Target Audience: "{audience}"
The video should be 3-4 scenes (under 30 seconds total).

If the audience is "Kids" or "Children", use a bright, exaggerated 3D cartoon/Pixar style. Make the characters funny (e.g., talking animals or silly creatures) and use clean, slapstick humor.

FIRST, choose the best FORMAT for this topic:
1. "story" (Dramatic/News narrator style)
2. "comedy" (A funny sketch/dialogue between two characters)
3. "pov" (Relatable meme style, text on screen, NO voiceover)

THEN, write the script.
For each scene, provide:
1. "image_prompt": A highly detailed prompt for an AI image generator. If comedy, make it expressive and funny.
2. "voiceover": The Hindi/Hinglish narration. If "pov", leave this blank. 
3. "character": If "comedy", specify "Character_A" or "Character_B". Otherwise, use "Narrator".
4. "text_on_screen": The text that should appear on the video.

Respond ONLY with a JSON object in this format:
{
  "format": "comedy",
  "scenes": [
    {
      "scene": 1,
      "image_prompt": "...",
      "voiceover": "...",
      "character": "Character_A",
      "text_on_screen": "..."
    }
  ]
}
"""

def generate_script(keyword, audience="General"):
    print(f"{Fore.CYAN}🧠 Asking Gemini to write a dynamic script for '{keyword}' (Audience: {audience})...{Fore.RESET}")
    response = model.generate_content(PROMPT_TEMPLATE.format(keyword=keyword, audience=audience))
    try:
        data = json.loads(response.text)
        print(f"{Fore.GREEN}✅ Script generated! Format chosen: {data['format'].upper()}{Fore.RESET}")
        return data
    except Exception as e:
        print(f"{Fore.RED}Failed to parse script: {e}{Fore.RESET}")
        print("Raw response:", response.text)
        return []

async def generate_audio_async(text, filepath, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

def generate_audio(text, filepath, voice="hi-IN-MadhurNeural"):
    asyncio.run(generate_audio_async(text, filepath, voice))

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

def stitch_video(scenes_data, output_filename, format_type):
    print(f"{Fore.YELLOW}🎬 Stitching {format_type.upper()} video together...{Fore.RESET}")
    clips = []
    
    for data in scenes_data:
        image_path = data['image_path']
        audio_path = data.get('audio_path')
        
        # Load audio if it exists, else set a default duration for POV
        if audio_path and os.path.exists(audio_path):
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            image_clip = ImageClip(image_path).set_duration(duration)
            image_clip = image_clip.set_audio(audio_clip)
        else:
            duration = 4.0 # default 4 seconds per scene for POV
            image_clip = ImageClip(image_path).set_duration(duration)
            
        # TODO: Add TextClip for text_on_screen
        
        clips.append(image_clip)
        
    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(output_filename, fps=24, codec="libx264", audio_codec="aac", logger=None)
    print(f"{Fore.GREEN}🎉 Video saved to {output_filename}{Fore.RESET}")

def run_type1_viral_pipeline(keyword, audience="General"):
    script_data = generate_script(keyword, audience)
    if not script_data:
        return
        
    format_type = script_data.get('format', 'story')
    scenes = script_data.get('scenes', [])
    scenes_data = []
    
    for i, scene in enumerate(scenes):
        print(f"\n{Fore.CYAN}--- Processing Scene {i+1} ---{Fore.RESET}")
        
        character = scene.get('character', 'Narrator')
        voiceover = scene.get('voiceover', '').strip()
        text_on_screen = scene.get('text_on_screen', '')
        
        print(f"Character: {character}")
        if voiceover:
            print(f"Dialogue: {voiceover}")
        if text_on_screen:
            print(f"Text: {text_on_screen}")
        
        audio_path = os.path.join(OUTPUT_DIR, "audio", f"scene_{i}.mp3")
        image_path = os.path.join(OUTPUT_DIR, "thumbnails", f"scene_{i}.jpg")
        
        if voiceover and format_type != 'pov':
            print(f"🎙️ Generating voiceover...")
            # Pick voice based on character
            voice = "hi-IN-SwaraNeural" if character == "Character_B" else "hi-IN-MadhurNeural"
            generate_audio(voiceover, audio_path, voice)
        else:
            audio_path = None
            
        print(f"🎨 Generating AI image (Comedy/Meme style)...")
        generate_image(scene['image_prompt'], image_path)
        
        scenes_data.append({
            "audio_path": audio_path,
            "image_path": image_path,
            "text": text_on_screen
        })
        
    output_video = os.path.join(OUTPUT_DIR, "videos", f"viral_{keyword.replace(' ', '_')}.mp4")
    stitch_video(scenes_data, output_video, format_type)
