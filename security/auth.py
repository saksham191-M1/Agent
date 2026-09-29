import bcrypt
from config.settings import JARVIS_PIN, JARVIS_PASSPHRASE
import logging

logger = logging.getLogger("JARVIS")

# Hardcoded hash of the env pin for demo/phase1
_stored_pin_hash = bcrypt.hashpw(JARVIS_PIN.encode('utf-8'), bcrypt.gensalt())

def verify_pin(input_pin: str) -> bool:
    try:
        if bcrypt.checkpw(input_pin.encode('utf-8'), _stored_pin_hash):
            logger.info("PIN verified successfully.")
            return True
        logger.warning("Failed PIN verification.")
        return False
    except Exception as e:
        logger.error(f"Error verifying PIN: {e}")
        return False

def verify_passphrase(input_text: str) -> bool:
    if not input_text:
        return False
    expected = JARVIS_PASSPHRASE.lower().strip().replace(".", "")
    actual = input_text.lower().strip().replace(".", "")
    if expected in actual:
        logger.info("Voice passphrase verified successfully.")
        return True
    logger.warning(f"Failed passphrase verification. Expected '{expected}', got '{actual}'")
    return False
