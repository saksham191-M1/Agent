import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont
from colorama import Fore, init

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import OUTPUT_DIR

init(autoreset=True)

async def generate_voiceover(text, filepath, voice="hi-IN-MadhurNeural"):
    """Generates the TTS audio."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

def create_caption_image(text, filepath, width=1080, height=1920):
    """
    Creates a transparent PNG with bold yellow text with a black stroke.
    Uses Pillow instead of MoviePy's TextClip to avoid ImageMagick dependencies on Windows.
    """
    # Create a transparent image
    img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to load a bold system font, fallback to default
    try:
        font = ImageFont.truetype("impact.ttf", 90)
    except IOError:
        try:
            font = ImageFont.truetype("arialbd.ttf", 90)
        except IOError:
            font = ImageFont.load_default()

    # Calculate text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Center position
    x = (width - text_w) / 2
    y = (height - text_h) / 2
    
    # Draw black stroke/outline
    stroke_width = 5
    for adj_x in range(-stroke_width, stroke_width+1):
        for adj_y in range(-stroke_width, stroke_width+1):
            draw.text((x+adj_x, y+adj_y), text, font=font, fill=(0, 0, 0, 255))
            
    # Draw main yellow text
    draw.text((x, y), text, font=font, fill=(255, 255, 0, 255))
    
    img.save(filepath)

def run_editor(video_path, voiceover_text, caption_text, output_filename):
    print(f"{Fore.CYAN}--- JARVIS EDITOR ENGINE ---{Fore.RESET}")
    
    # 1. Generate Voiceover
    print(f"{Fore.YELLOW}🎙️ Generating voiceover...{Fore.RESET}")
    audio_path = os.path.join(OUTPUT_DIR, "audio", "temp_voiceover.mp3")
    asyncio.run(generate_voiceover(voiceover_text, audio_path))
    
    # 2. Generate Caption Image
    print(f"{Fore.YELLOW}📝 Rendering bold captions...{Fore.RESET}")
    caption_path = os.path.join(OUTPUT_DIR, "thumbnails", "temp_caption.png")
    create_caption_image(caption_text, caption_path)
    
    # 3. Load Clips
    print(f"{Fore.YELLOW}🎬 Syncing timeline...{Fore.RESET}")
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip(video_path)
    
    # 4. Sync lengths (Loop video if audio is longer, trim if video is longer)
    if video_clip.duration < audio_clip.duration:
        # Loop video to match audio length
        video_clip = video_clip.fx(vfx.loop, duration=audio_clip.duration)
    else:
        # Trim video to audio length
        video_clip = video_clip.subclip(0, audio_clip.duration)
        
    # 5. Overlay Caption
    caption_clip = ImageClip(caption_path).set_duration(audio_clip.duration)
    
    # Composite video and caption
    final_video = CompositeVideoClip([video_clip, caption_clip])
    
    # Attach audio
    final_video = final_video.set_audio(audio_clip)
    
    # Output path
    output_path = os.path.join(OUTPUT_DIR, "videos", output_filename)
    
    print(f"{Fore.GREEN}⚙️ Rendering final video...{Fore.RESET}")
    final_video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", logger=None)
    
    print(f"{Fore.GREEN}✅ Boom! Video successfully rendered to: {output_path}{Fore.RESET}")

if __name__ == "__main__":
    # Test block
    video_in = input("Enter raw video filename in input/raw_videos/ (e.g. saas.mp4): ")
    video_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "input", "raw_videos", video_in)
    
    if not os.path.exists(video_path):
        print(f"{Fore.RED}Error: Could not find {video_path}{Fore.RESET}")
        sys.exit(1)
        
    voice_txt = input("Enter voiceover script: ")
    caption_txt = input("Enter bold screen text: ")
    
    run_editor(video_path, voice_txt, caption_txt, f"FINAL_{video_in}")
