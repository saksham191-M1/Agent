import os
import sys
import base64
import requests
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont
from colorama import Fore, init

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import OUTPUT_DIR

init(autoreset=True)
load_dotenv()

def generate_voice_and_timestamps(text, audio_filepath):
    """Generates audio and word-level timestamps using ElevenLabs API."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print(f"{Fore.RED}❌ Error: ELEVENLABS_API_KEY not found in .env!{Fore.RESET}")
        sys.exit(1)
        
    # Using a premium highly energetic voice (e.g. Adam or generic)
    voice_id = "pNInz6obpgDQGcFmaJgB" # Adam (popular narrative voice)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        print(f"{Fore.RED}❌ ElevenLabs API Error: {response.text}{Fore.RESET}")
        sys.exit(1)
        
    response_json = response.json()
    
    # Save Audio
    audio_bytes = base64.b64decode(response_json["audio_base64"])
    with open(audio_filepath, "wb") as f:
        f.write(audio_bytes)
        
    # Parse Timestamps into Words
    alignment = response_json["alignment"]
    words = []
    current_word = ""
    start_time = None
    
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
                words.append({
                    "word": current_word.strip(),
                    "start": start_time if start_time is not None else 0.0,
                    "end": end_time
                })
            current_word = ""
            start_time = None
        else:
            if current_word == "":
                start_time = starts[i]
            current_word += char
            
    return words

def create_transparent_text_clip(text, duration, width=1080, height=1920):
    """Creates an ImageClip of bold text with a stroke."""
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("impact.ttf", 100)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", 100)
        except IOError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) / 2
    y = (height - text_h) / 2 + 200 
    
    stroke_width = 6
    for adj_x in range(-stroke_width, stroke_width+1):
        for adj_y in range(-stroke_width, stroke_width+1):
            draw.text((x+adj_x, y+adj_y), text, font=font, fill=(0, 0, 0, 255))
            
    draw.text((x, y), text, font=font, fill=(255, 255, 0, 255))
    
    temp_path = os.path.join(OUTPUT_DIR, "thumbnails", f"temp_txt.png")
    img.save(temp_path)
    
    return ImageClip(temp_path).set_duration(duration)

def run_ad_editor(video_path, voiceover_text, output_filename):
    print(f"{Fore.CYAN}--- JARVIS AD PERFECTION ENGINE (ELEVENLABS) ---{Fore.RESET}")
    
    audio_path = os.path.join(OUTPUT_DIR, "audio", "ad_voiceover.mp3")
    
    print(f"{Fore.YELLOW}🎙️ Fetching Hollywood Voice & Timestamps from ElevenLabs...{Fore.RESET}")
    words_data = generate_voice_and_timestamps(voiceover_text, audio_path)
    
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip(video_path)
    
    if video_clip.duration < audio_clip.duration:
        video_clip = video_clip.fx(vfx.loop, duration=audio_clip.duration)
    else:
        video_clip = video_clip.subclip(0, audio_clip.duration)
        
    print(f"{Fore.YELLOW}📝 Processing kinetic typography (word-by-word)...{Fore.RESET}")
    
    caption_clips = []
    current_chunk_text = []
    chunk_start_time = 0.0
    
    for i, w_data in enumerate(words_data):
        word = w_data["word"]
        start = w_data["start"]
        end = w_data["end"]
        
        if len(current_chunk_text) == 0:
            chunk_start_time = start
            
        current_chunk_text.append(word)
        
        if len(current_chunk_text) == 2 or word.endswith(('.', '?', '!', ',')) or i == len(words_data) - 1:
            duration = end - chunk_start_time
            text_str = " ".join(current_chunk_text).upper()
            
            txt_clip = create_transparent_text_clip(text_str, duration).set_start(chunk_start_time).set_position('center')
            caption_clips.append(txt_clip)
            current_chunk_text = []

    print(f"{Fore.YELLOW}🎬 Compositing dynamic captions over video...{Fore.RESET}")
    final_video = CompositeVideoClip([video_clip] + caption_clips)
    final_video = final_video.set_audio(audio_clip)
    
    output_path = os.path.join(OUTPUT_DIR, "videos", output_filename)
    
    print(f"{Fore.GREEN}⚙️ Rendering final Ad video...{Fore.RESET}")
    final_video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", logger=None)
    
    print(f"{Fore.GREEN}✅ Boom! Perfected Ad successfully rendered to: {output_path}{Fore.RESET}")

if __name__ == "__main__":
    video_in = input("Enter raw video filename in input/raw_videos/ (e.g. saas.mp4): ")
    video_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "raw_videos", video_in)
    
    if not os.path.exists(video_path):
        print(f"{Fore.RED}Error: Could not find {video_path}{Fore.RESET}")
        sys.exit(1)
        
    voice_txt = input("Enter the full voiceover script: ")
    
    run_ad_editor(video_path, voice_txt, f"AD_PERFECT_{video_in}")
