import logging
import os
from typing import Optional

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None

logger = logging.getLogger(__name__)

class VoiceSystem:
    """Voice processing system for speech-to-text and text-to-speech"""
    
    def __init__(self):
        self.tts_engine = None
        self.available = False
        self.last_error = None
        self.init_tts()
    
    def init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            if os.getenv("VIRA_ENABLE_TTS", "").lower() not in {"1", "true", "yes"}:
                self.last_error = "TTS disabled by default for backend stability"
                self.available = False
                logger.info(self.last_error)
                return

            if pyttsx3 is None:
                self.last_error = "pyttsx3 is not installed"
                self.available = False
                logger.warning(self.last_error)
                return

            self.tts_engine = pyttsx3.init()
            # Configure voice properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)  # Use first available voice
            self.tts_engine.setProperty('rate', 150)  # Words per minute
            self.tts_engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)
            self.available = True
            self.last_error = None
            logger.info("Text-to-speech engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.tts_engine = None
            self.available = False
            self.last_error = str(e)

    def text_to_speech(self, text: str, speak: bool = True) -> Optional[str]:
        """Convert text to speech"""
        try:
            if not self.tts_engine or not self.available:
                return "Text-to-speech not available"
            
            if speak:
                logger.info("Voice output requested, but live audio playback is disabled for backend stability")
                return "Voice output is available in preview mode, but live playback is disabled to keep the API stable."
            else:
                # Just return the text (for testing)
                return text
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            self.available = False
            self.last_error = str(e)
            return f"Error in TTS: {str(e)}"
    
    def speech_to_text(self, audio_file: Optional[str] = None) -> str:
        """Convert speech to text (placeholder - would integrate with speech recognition)"""
        # In a real implementation, this would use speech recognition
        if audio_file:
            return f"Speech recognition for file: {audio_file} (requires speech recognition library)"
        else:
            return "Speech recognition not yet implemented - requires microphone access and speech recognition library"
    
    def set_voice_properties(self, rate: int = 150, volume: float = 0.8, voice_id: int = 0):
        """Set voice properties"""
        try:
            if self.tts_engine:
                self.tts_engine.setProperty('rate', rate)
                self.tts_engine.setProperty('volume', volume)
                voices = self.tts_engine.getProperty('voices')
                if voices and voice_id < len(voices):
                    self.tts_engine.setProperty('voice', voices[voice_id].id)
                self.available = True
                self.last_error = None
                return "Voice properties updated successfully"
            else:
                return "TTS engine not available"
        except Exception as e:
            self.available = False
            self.last_error = str(e)
            return f"Error setting voice properties: {str(e)}"

# Global voice instance
voice_system = VoiceSystem()
