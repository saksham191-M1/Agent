import speech_recognition as sr
import whisper
import os
import tempfile
import logging
from colorama import Fore

logger = logging.getLogger("JARVIS")

print(f"{Fore.CYAN}Loading Whisper model (small)... this might take a moment the first time.{Fore.RESET}")
# Using base or small for fast transcription on CPU/GPU
try:
    _whisper_model = whisper.load_model("base")
    print(f"{Fore.GREEN}Whisper model loaded successfully.{Fore.RESET}")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    _whisper_model = None

def listen_once() -> str:
    """Listens to the microphone and transcribes using Whisper."""
    if not _whisper_model:
        return ""
        
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"{Fore.CYAN}🎤 Listening... Speak now!{Fore.RESET}")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            # Listen for up to 10 seconds
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
            print(f"{Fore.YELLOW}Processing speech...{Fore.RESET}")
            
            # Save temporary wav
            temp_wav = os.path.join(tempfile.gettempdir(), "temp_voice_input.wav")
            with open(temp_wav, "wb") as f:
                f.write(audio.get_wav_data())
            
            # Transcribe with whisper (fp16=False is safer for CPU inference)
            result = _whisper_model.transcribe(temp_wav, fp16=False)
            os.remove(temp_wav)
            
            text = result["text"].strip()
            print(f"{Fore.GREEN}Transcribed: {text}{Fore.RESET}")
            return text
        except sr.WaitTimeoutError:
            print(f"{Fore.RED}Listening timed out. No speech detected.{Fore.RESET}")
            return ""
        except Exception as e:
            logger.error(f"Error in listen_once: {e}")
            return ""
