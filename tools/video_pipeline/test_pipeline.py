import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Add jarvis root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from type1_ai.product_ad_ai import generate_ad_script, generate_ad_image
from type1_ai.viral_ai import generate_audio, stitch_video
from config.settings import OUTPUT_DIR
import os

def test_pipeline():
    print("=== Testing Pipeline ===")
    
    # 1. Test Script Generation
    print("\n1. Testing Gemini Script Generation...")
    script_data = generate_ad_script("Test Coffee", "Low Energy", "Buy Now")
    assert script_data is not None, "Script generation failed!"
    assert 'scenes' in script_data, "Script JSON format is incorrect!"
    print("-> Script generation OK")
    
    # 2. Test Image Generation
    print("\n2. Testing Image Generation (API)...")
    img_path = os.path.join(OUTPUT_DIR, "thumbnails", "test_img.jpg")
    generate_ad_image("A delicious cup of coffee, cinematic lighting", img_path)
    assert os.path.exists(img_path), "Image file was not created!"
    assert os.path.getsize(img_path) > 1000, "Image file is too small! (Probably HTML error)"
    print("-> Image generation OK")
    
    # 3. Test Audio Generation
    print("\n3. Testing Audio Generation (Edge-TTS)...")
    aud_path = os.path.join(OUTPUT_DIR, "audio", "test_aud.mp3")
    generate_audio("Hello, this is a test audio for the coffee advertisement.", aud_path)
    assert os.path.exists(aud_path), "Audio file was not created!"
    assert os.path.getsize(aud_path) > 1000, "Audio file is too small!"
    print("-> Audio generation OK")
    
    # 4. Test Stitching
    print("\n4. Testing Video Stitching (MoviePy)...")
    vid_path = os.path.join(OUTPUT_DIR, "videos", "test_video.mp4")
    scenes_data = [{"image_path": img_path, "audio_path": aud_path, "text": "TEST"}]
    try:
        stitch_video(scenes_data, vid_path, format_type="ad")
        assert os.path.exists(vid_path), "Video file was not created!"
        print("-> Video stitching OK")
    except Exception as e:
        print(f"Stitching failed: {e}")
        sys.exit(1)
        
    print("\n✅ All Tests Passed Successfully!")

if __name__ == "__main__":
    test_pipeline()
