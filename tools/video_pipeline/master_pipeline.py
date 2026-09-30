import os
import sys
import json
import time
from colorama import Fore, init

sys.stdout.reconfigure(encoding='utf-8')
init(autoreset=True)

# Append paths so we can import our custom modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "tools", "browser_agent"))

from config.settings import OUTPUT_DIR
from tools.video_pipeline.brain_opus import generate_multi_scene_blueprint
from tools.browser_agent.gemini_flow import generate_veo_media
from tools.video_pipeline.manus_launch_engine import run_manus_engine

def run_master_pipeline(app_name):
    print(f"\n{Fore.MAGENTA}===================================================={Fore.RESET}")
    print(f"{Fore.MAGENTA}🚀 JARVIS MASTER PIPELINE: INITIALIZING '{app_name.upper()}'{Fore.RESET}")
    print(f"{Fore.MAGENTA}===================================================={Fore.RESET}\n")

    # --- STEP 1: THE BRAIN ---
    print(f"{Fore.CYAN}[STEP 1] Opus Director Brain generating Multi-Scene Blueprint...{Fore.RESET}")
    raw_blueprint = generate_multi_scene_blueprint(app_name)
    
    # Clean JSON
    cleaned_json = raw_blueprint.replace('```json', '').replace('```', '').strip()
    blueprint = json.loads(cleaned_json)
    
    print(f"{Fore.GREEN}✅ Blueprint created! Selected Template: {blueprint['selected_template']}{Fore.RESET}\n")
    
    # --- STEP 2: THE BROWSER AGENT (CREW) ---
    raw_video_dir = os.path.join(PROJECT_ROOT, "input", "raw_videos")
    os.makedirs(raw_video_dir, exist_ok=True)
    
    generated_videos = []
    full_voiceover_script = ""
    
    for scene in blueprint['scenes']:
        scene_id = scene['scene_id']
        prompt = scene['veo_prompt']
        voiceover = scene['voiceover']
        
        print(f"{Fore.YELLOW}🎬 Preparing Scene {scene_id}...{Fore.RESET}")
        
        # Build the final script
        full_voiceover_script += voiceover + " "
        
        # Generate and Download Veo Video
        output_filename = f"{app_name.lower().replace(' ', '_')}_scene_{scene_id}.mp4"
        output_filepath = os.path.join(raw_video_dir, output_filename)
        
        if not os.path.exists(output_filepath):
            print(f"{Fore.CYAN}   -> Dispatching Playwright to download Veo media...{Fore.RESET}")
            # generate_veo_media(prompt, output_filepath)
            print(f"{Fore.GREEN}   -> [SIMULATED] Successfully downloaded {output_filename}{Fore.RESET}")
        else:
            print(f"{Fore.GREEN}   -> Video {output_filename} already exists. Skipping download.{Fore.RESET}")
            
        generated_videos.append(output_filename)
        print()
        time.sleep(1) # Small pause for rate limits

    # --- STEP 3: THE ENGINE (EDITOR) ---
    print(f"{Fore.CYAN}[STEP 3] Stitching scenes with Manus Editor Engine...{Fore.RESET}")
    
    # NOTE: The current manus_launch_engine expects a single video input. 
    # To truly stitch 4 videos, we would use MoviePy's concatenate_videoclips.
    # For this master run, we will pass the primary scene (Scene 1 or 2) into the engine 
    # to render the final Opus-level visual style.
    
    primary_video = generated_videos[1] if len(generated_videos) > 1 else generated_videos[0]
    final_output_name = f"FINAL_AD_{app_name.lower().replace(' ', '_')}.mp4"
    
    print(f"{Fore.YELLOW}   -> Injecting ElevenLabs Voiceover & Kinetic Typography...{Fore.RESET}")
    
    # We call our god-tier Engine
    # run_manus_engine(primary_video, full_voiceover_script, final_output_name)
    print(f"{Fore.GREEN}   -> [SIMULATED] Engine Render Complete!{Fore.RESET}")
    
    final_path = os.path.join(OUTPUT_DIR, "videos", final_output_name)
    print(f"\n{Fore.MAGENTA}🎉 SUCCESS! Master Pipeline finished.{Fore.RESET}")
    print(f"{Fore.WHITE}Final Video Output: {final_path}{Fore.RESET}")

if __name__ == "__main__":
    target_app = sys.argv[1] if len(sys.argv) > 1 else "Swiggy"
    run_master_pipeline(target_app)
