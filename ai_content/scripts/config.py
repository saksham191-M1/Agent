import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory for ai_content (anchor everything here)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

# Directories
PROMPTS_DIR = BASE_DIR / "prompts"
TEMPLATES_DIR = PROMPTS_DIR / "templates"
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
RAW_RENDERS_DIR = OUTPUT_DIR / "renders" / "raw"
FINAL_RENDERS_DIR = OUTPUT_DIR / "renders" / "final"
TEMP_ECPROJ_DIR = OUTPUT_DIR / "temp_ecproj"
METRICS_DIR = OUTPUT_DIR / "metrics"
AUDIO_DIR = OUTPUT_DIR / "audio"

# Ensure runtime directories exist
for directory in [INPUT_DIR, OUTPUT_DIR, RAW_RENDERS_DIR, FINAL_RENDERS_DIR, TEMP_ECPROJ_DIR, METRICS_DIR, AUDIO_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configuration keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_FLOW_URL = os.getenv("GOOGLE_FLOW_URL", "https://flow.google.com/")
HEADLESS = os.getenv("HEADLESS", "False").lower() in ("true", "1", "yes")
STORAGE_STATE_PATH = Path(os.getenv("STORAGE_STATE_PATH", str(BASE_DIR / "storage_state.json"))).resolve()
EFFECTCRAFT_CLI_PATH = os.getenv("EFFECTCRAFT_CLI_PATH", "")
