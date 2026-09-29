import os
import sys
import asyncio
import edge_tts
import webvtt
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont
from colorama import Fore, init

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import OUTPUT_DIR

init(autoreset=True)

async def generate_voice_and_subs(text, audio_filepath, vtt_filepath, voice="hi-IN-MadhurNeural"):
    """Generates audio and word-level VTT subtitles simultaneously."""
    communicate = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()
    
    with open(audio_filepath, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])
                
    with open(vtt_filepath, "w", encoding="utf-8") as vtt_file:
        vtt_file.write(submaker.generate_subs())

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
    
    # Center text horizontally, slightly below center vertically
    x = (width - text_w) / 2
    y = (height - text_h) / 2 + 200 
    
    # Draw black outline
    stroke_width = 6
    for adj_x in range(-stroke_width, stroke_width+1):
        for adj_y in range(-stroke_width, stroke_width+1):
            draw.text((x+adj_x, y+adj_y), text, font=font, fill=(0, 0, 0, 255))
            
    # Draw yellow text
    draw.text((x, y), text, font=font, fill=(255, 255, 0, 255))
    
    # Save temp image
    temp_path = os.path.join(OUTPUT_DIR, "thumbnails", f"temp_txt.png")
    img.save(temp_path)
    
    return ImageClip(temp_path).set_duration(duration)

def run_ad_editor(video_path, voiceover_text, output_filename):
    print(f"{Fore.CYAN}--- JARVIS AD PERFECTION ENGINE ---{Fore.RESET}")
    
    audio_path = os.path.join(OUTPUT_DIR, "audio", "ad_voiceover.mp3")
    vtt_path = os.path.join(OUTPUT_DIR, "audio", "ad_voiceover.vtt")
    
    print(f"{Fore.YELLOW}🎙️ Generating energetic voiceover and extracting word timestamps...{Fore.RESET}")
    asyncio.run(generate_voice_and_subs(voiceover_text, audio_path, vtt_path))
    
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip(video_path)
    
    # Sync video length to audio length
    if video_clip.duration < audio_clip.duration:
        video_clip = video_clip.fx(vfx.loop, duration=audio_clip.duration)
    else:
        video_clip = video_clip.subclip(0, audio_clip.duration)
        
    print(f"{Fore.YELLOW}📝 Processing kinetic typography (word-by-word)...{Fore.RESET}")
    
    # Read VTT file
    subs = webvtt.read(vtt_path)
    caption_clips = []
    
    def time_to_seconds(t_str):
        h, m, s = t_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    
    # Group words into chunks of 2 for better readability
    current_chunk_text = []
    chunk_start_time = 0.0
    
    for i, sub in enumerate(subs):
        start = time_to_seconds(sub.start)
        end = time_to_seconds(sub.end)
        word = sub.text.strip()
        
        if len(current_chunk_text) == 0:
            chunk_start_time = start
            
        current_chunk_text.append(word)
        
        # If we have 2 words, or it's the end of a sentence, or the last word
        if len(current_chunk_text) == 2 or word.endswith(('.', '?', '!', ',')) or i == len(subs) - 1:
            duration = end - chunk_start_time
            text_str = " ".join(current_chunk_text).upper()
            
            # Generate the text image clip
            txt_clip = create_transparent_text_clip(text_str, duration).set_start(chunk_start_time).set_position('center')
            caption_clips.append(txt_clip)
            
            # Reset for next chunk
            current_chunk_text = []

    print(f"{Fore.YELLOW}🎬 Compositing {len(caption_clips)} dynamic captions over video...{Fore.RESET}")
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
