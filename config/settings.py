import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

# Specific paths
DB_PATH = DATA_DIR / "jarvis.db"
VOICES_DIR = ASSETS_DIR / "voices"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(VOICES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR / "videos", exist_ok=True)
os.makedirs(OUTPUT_DIR / "thumbnails", exist_ok=True)
os.makedirs(OUTPUT_DIR / "audio", exist_ok=True)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
JARVIS_PASSPHRASE = os.getenv("JARVIS_PASSPHRASE", "jarvis initialize")
JARVIS_PIN = os.getenv("JARVIS_PIN", "1234")
VOICE_OUTPUT_ENABLED = os.getenv("VOICE_OUTPUT", "true").lower() == "true"
