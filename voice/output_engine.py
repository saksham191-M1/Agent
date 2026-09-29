import edge_tts
import asyncio
import os
import pygame
import tempfile
import logging

logger = logging.getLogger("JARVIS")

# Initialize pygame mixer for audio playback
pygame.mixer.init()

async def _generate_audio(text, voice="hi-IN-MadhurNeural", output_file="temp_output.mp3"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def speak(text, voice="hi-IN-MadhurNeural"):
    """Generates TTS audio and plays it synchronously."""
    try:
        temp_file = os.path.join(tempfile.gettempdir(), "jarvis_speak.mp3")
        # Run async edge_tts generation
        asyncio.run(_generate_audio(text, voice, temp_file))
        
        # Play the audio file
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        # Wait for the audio to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        # Clean up
        pygame.mixer.music.unload()
        try:
            os.remove(temp_file)
        except OSError:
            pass # Ignore file in use errors
    except Exception as e:
        logger.error(f"Error in speech generation: {e}")
