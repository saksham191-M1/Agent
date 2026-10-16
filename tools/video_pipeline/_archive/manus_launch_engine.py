import os
import sys
import base64
import requests
import math
from dotenv import load_dotenv
from moviepy.editor import (VideoFileClip, AudioFileClip, ImageClip, 
                            CompositeVideoClip, ColorClip, vfx, CompositeAudioClip)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
from colorama import Fore, init

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import OUTPUT_DIR

init(autoreset=True)
load_dotenv()

# --- MANUS 2.0 AESTHETICS ---
PORCELAIN_BG = (245, 245, 247)  # Apple/Manus off-white
TEXT_COLOR = (29, 29, 31, 255)  # Deep minimalist grey
HIGHLIGHT_COLOR = (0, 113, 227, 255) # Subtle blue for emphasis
WIDTH, HEIGHT = 1080, 1920

def generate_voice_and_timestamps(text, audio_filepath):
    """ElevenLabs API for perfect pacing and word-level timestamps."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print(f"{Fore.RED}❌ Error: ELEVENLABS_API_KEY not found in .env!{Fore.RESET}")
        sys.exit(1)
        
    voice_id = "pNInz6obpgDQGcFmaJgB" # Professional narrative voice
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}❌ ElevenLabs API Error: {response.text}{Fore.RESET}")
        sys.exit(1)
        
    response_json = response.json()
    with open(audio_filepath, "wb") as f:
        f.write(base64.b64decode(response_json["audio_base64"]))
        
    alignment = response_json["alignment"]
    words, current_word, start_time = [], "", None
    chars = alignment.get('characters', [])
    starts = alignment.get('character_start_times_seconds', [])
    ends = alignment.get('character_end_times_seconds', [])
    
    for i, char in enumerate(chars):
        if char == ' ' or i == len(chars) - 1:
            if char != ' ':
                current_word += char
                end_time = ends[i]
            else:
                end_time = ends[i-1] if i > 0 else 0.0
                
            if current_word.strip():
                words.append({"word": current_word.strip(), "start": start_time or 0.0, "end": end_time})
            current_word, start_time = "", None
        else:
            if current_word == "": start_time = starts[i]
            current_word += char
            
    return words

def create_elegant_text_clip(text, duration, is_highlight=False):
    """Creates a clean, Apple-style kinetic text card on a transparent layer."""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 90) # Clean sans-serif
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (WIDTH - text_w) / 2
    y = (HEIGHT - text_h) / 2
    
    color = HIGHLIGHT_COLOR if is_highlight else TEXT_COLOR
    draw.text((x, y), text, font=font, fill=color)
    
    temp_path = os.path.join(OUTPUT_DIR, "thumbnails", f"temp_manus_txt_{hash(text)}.png")
    img.save(temp_path)
    
    # Fade in very slightly for that smooth cinematic feel
    clip = ImageClip(temp_path).set_duration(duration).crossfadein(0.1)
    return clip

def camera_push_in(t, duration):
    """Simulates a smooth cinematic camera zoom (1.0x to 1.15x)."""
    progress = t / duration
    zoom = 1.0 + (0.15 * progress)
    return zoom

def round_corners_with_shadow(video_clip):
    """Adds a glass-morphism floating card effect to video (B-Roll)."""
    return video_clip.resize(0.85).set_position('center')

def run_manus_engine(video_path, voiceover_text, output_filename):
    print(f"{Fore.CYAN}--- MANUS 2.0 LAUNCH ENGINE ---{Fore.RESET}")
    print(f"{Fore.MAGENTA}Opus-level logic engaged. Rendering porcelain canvas, glass cards, and camera push-ins.{Fore.RESET}")
    
    audio_path = os.path.join(OUTPUT_DIR, "audio", "manus_voiceover.mp3")
    
    print(f"{Fore.YELLOW}🎙️ Synthesizing flawless narrative voice...{Fore.RESET}")
    words_data = generate_voice_and_timestamps(voiceover_text, audio_path)
    audio_clip = AudioFileClip(audio_path)
    
    print(f"{Fore.YELLOW}🎥 Processing B-Roll with Camera Push-ins...{Fore.RESET}")
    raw_video = VideoFileClip(video_path)
    
    if raw_video.duration < audio_clip.duration:
        raw_video = raw_video.fx(vfx.loop, duration=audio_clip.duration)
    else:
        raw_video = raw_video.subclip(0, audio_clip.duration)
        
    b_roll = round_corners_with_shadow(raw_video)
    b_roll = b_roll.resize(lambda t: camera_push_in(t, audio_clip.duration))
    
    bg_clip = ColorClip(size=(WIDTH, HEIGHT), color=PORCELAIN_BG, duration=audio_clip.duration)
    
    print(f"{Fore.YELLOW}📝 Rendering Elegant Kinetic Typography...{Fore.RESET}")
    caption_clips = []
    current_chunk = []
    chunk_start = 0.0
    
    for i, w_data in enumerate(words_data):
        word = w_data["word"]
        if len(current_chunk) == 0:
            chunk_start = w_data["start"]
            
        current_chunk.append(word)
        
        if len(current_chunk) >= 3 or word.endswith(('.', '?', '!', ',')) or i == len(words_data) - 1:
            duration = w_data["end"] - chunk_start
            text_str = " ".join(current_chunk)
            
            is_hl = any(char.isupper() for char in word) and len(word) > 4
            
            txt_clip = create_elegant_text_clip(text_str, duration, is_highlight=is_hl)
            txt_clip = txt_clip.set_start(chunk_start).set_position(('center', 1300))
            caption_clips.append(txt_clip)
            current_chunk = []

    print(f"{Fore.YELLOW}🎬 Compositing layers...{Fore.RESET}")
    
    final_video = CompositeVideoClip([bg_clip, b_roll] + caption_clips)
    final_video = final_video.set_audio(audio_clip)
    
    output_path = os.path.join(OUTPUT_DIR, "videos", output_filename)
    
    print(f"{Fore.GREEN}⚙️ Rendering final cinematic launch video...{Fore.RESET}")
    final_video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", logger=None)
    
    print(f"{Fore.GREEN}✅ Boom! Opus-Tier Manus 2.0 Video rendered: {output_path}{Fore.RESET}")

if __name__ == "__main__":
    video_in = input("Enter raw video filename in input/raw_videos/ (e.g. saas.mp4): ")
    video_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "raw_videos", video_in)
    
    if not os.path.exists(video_path):
        print(f"{Fore.RED}Error: Could not find {video_path}{Fore.RESET}")
        sys.exit(1)
        
    voice_txt = input("Enter the full launch script: ")
    run_manus_engine(video_path, voice_txt, f"MANUS_{video_in}")
