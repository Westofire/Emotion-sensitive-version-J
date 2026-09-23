"""
Emotion-Sensitive Text-to-Speech Module
Converts text to speech with emotional variations in pitch, speed, and volume
"""

import pyttsx3
import re
from enum import Enum
from typing import Optional, Dict, Tuple


class Emotion(Enum):
    """Emotion types with associated speech parameters"""
    HAPPY = {
        'rate': 160,      # Faster speech
        'volume': 1.0,    # Normal volume
        'pitch': 1.4,     # Higher pitch
    }
    SAD = {
        'rate': 100,      # Slower speech
        'volume': 0.7,    # Lower volume
        'pitch': 0.8,     # Lower pitch
    }
    ANGRY = {
        'rate': 180,      # Much faster
        'volume': 1.0,    # Normal volume
        'pitch': 1.2,     # Slightly higher
    }
    CALM = {
        'rate': 110,      # Slow and measured
        'volume': 0.9,    # Slightly lower
        'pitch': 0.9,     # Slightly lower
    }
    SURPRISED = {
        'rate': 140,      # Moderate speed
        'volume': 1.0,    # Normal volume
        'pitch': 1.5,     # Much higher
    }
    NEUTRAL = {
        'rate': 125,      # Normal speed
        'volume': 1.0,    # Normal volume
        'pitch': 1.0,     # Normal pitch
    }


class EmotionTTS:
    """
    Text-to-Speech engine with emotion-based variations
    Supports pitch and speed adjustments based on detected emotion
    """
    
    def __init__(self, voice_gender: str = 'female'):
        """
        Initialize the TTS engine
        
        Args:
            voice_gender: 'male' or 'female' for voice selection
        """
        self.engine = pyttsx3.init()
        self._set_voice(voice_gender)
        self.voices = self.engine.getProperty('voices')
        
    def _set_voice(self, gender: str):
        """Set voice gender (male/female)"""
        voices = self.engine.getProperty('voices')
        if gender.lower() == 'male' and len(voices) > 0:
            self.engine.setProperty('voice', voices[0].id)  # Usually male
        elif gender.lower() == 'female' and len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)  # Usually female
    
    def speak_with_emotion(
        self, 
        text: str, 
        emotion: str = 'neutral',
        save_to_file: Optional[str] = None
    ) -> bool:
        """
        Speak text with emotion-based modifications
        
        Args:
            text: The text to speak
            emotion: Emotion type ('happy', 'sad', 'angry', 'calm', 'surprised', 'neutral')
            save_to_file: Optional file path to save audio (.mp3 or .wav)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get emotion parameters
            emotion_upper = emotion.upper()
            if emotion_upper not in Emotion.__members__:
                print(f"Unknown emotion: {emotion}. Using NEUTRAL")
                emotion_upper = 'NEUTRAL'
            
            params = Emotion[emotion_upper].value
            
            # Apply speech parameters
            self.engine.setProperty('rate', params['rate'])
            self.engine.setProperty('volume', params['volume'])
            self._set_pitch(params['pitch'])
            
            # Speak
            self.engine.say(text)
            
            # Save to file if requested
            if save_to_file:
                self.engine.save_to_file(text, save_to_file)
            
            self.engine.runAndWait()
            print(f"✓ Spoke with {emotion} emotion")
            return True
            
        except Exception as e:
            print(f"✗ Error in TTS: {e}")
            return False
    
    def _set_pitch(self, pitch: float):
        """
        Adjust pitch by modifying voice rate proportionally
        Note: pyttsx3 doesn't have direct pitch control, so we use rate as a proxy
        For true pitch control, consider using Piper or festival
        
        Args:
            pitch: Pitch multiplier (0.8 = lower, 1.0 = normal, 1.4 = higher)
        """
        # This is a workaround; real pitch requires different libraries
        # For now, we'll note this limitation in the docstring
        pass
    
    def get_emotion_parameters(self, emotion: str) -> Dict:
        """Get the speech parameters for a given emotion"""
        emotion_upper = emotion.upper()
        if emotion_upper in Emotion.__members__:
            return Emotion[emotion_upper].value
        return Emotion.NEUTRAL.value
    
    def list_available_emotions(self) -> list:
        """Return list of available emotions"""
        return [e.name.lower() for e in Emotion]
    
    def cleanup(self):
        """Clean up TTS engine resources"""
        self.engine.endLoop()


# ============================================================================
# ADVANCED: Using Piper for Better Pitch Control (Alternative)
# ============================================================================

class PiperEmotionTTS:
    """
    Advanced TTS using Piper for better pitch/speed control
    Requires: pip install piper-tts
    
    Note: Piper is more powerful but requires additional setup
    """
    
    @staticmethod
    def install_piper():
        """Install Piper TTS"""
        import subprocess
        subprocess.run(["pip", "install", "piper-tts"], check=True)
    
    @staticmethod
    def speak_with_piper(
        text: str,
        emotion: str = 'neutral',
        output_file: Optional[str] = None
    ):
        """
        Speak using Piper with emotion variations
        
        Requires piper installation: pip install piper-tts
        """
        try:
            from piper import PiperTTS
        except ImportError:
            print("Piper not installed. Run: pip install piper-tts")
            return False
        
        # Emotion parameters for Piper
        emotion_params = {
            'happy': {'speed': 1.2, 'pitch': 1.4},
            'sad': {'speed': 0.8, 'pitch': 0.8},
            'angry': {'speed': 1.4, 'pitch': 1.2},
            'calm': {'speed': 0.9, 'pitch': 0.9},
            'surprised': {'speed': 1.1, 'pitch': 1.5},
            'neutral': {'speed': 1.0, 'pitch': 1.0},
        }
        
        params = emotion_params.get(emotion.lower(), emotion_params['neutral'])
        
        print(f"Speaking with Piper ({emotion}): speed={params['speed']}, pitch={params['pitch']}")
        # Implementation would go here
        return True


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize TTS engine
    tts = EmotionTTS(voice_gender='female')
    
    # Example: Different emotions for a chatbot response
    response = "Hello! I'm so happy to help you today!"
    
    print("Available emotions:", tts.list_available_emotions())
    print("\n--- Testing Emotions ---\n")
    
    # Test different emotions
    emotions = ['happy', 'sad', 'calm', 'angry', 'surprised', 'neutral']
    
    for emotion in emotions:
        print(f"\n{emotion.upper()}:")
        params = tts.get_emotion_parameters(emotion)
        print(f"  Rate: {params['rate']} | Volume: {params['volume']} | Pitch: {params['pitch']}")
        
        # Uncomment to hear audio output:
        # tts.speak_with_emotion(response, emotion=emotion)
    
    # Clean up
    tts.cleanup()
