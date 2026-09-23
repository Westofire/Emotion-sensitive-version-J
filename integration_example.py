"""
Integration Example: Emotion-Sensitive Chatbot with TTS
Shows how to combine emotion detection with text-to-speech
"""

from emotion_tts import EmotionTTS, Emotion
from typing import Tuple


class EmotionSensitiveChatbot:
    """
    Example chatbot that detects emotions and speaks with appropriate voice
    """
    
    def __init__(self, voice_gender: str = 'female'):
        self.tts = EmotionTTS(voice_gender=voice_gender)
        self.conversation_history = []
    
    def detect_emotion_from_response(self, text: str) -> str:
        """
        Simple emotion detection based on keywords
        In real implementation, use NLP models (transformers, etc.)
        
        Args:
            text: The chatbot's response text
            
        Returns:
            Detected emotion as string
        """
        text_lower = text.lower()
        
        # Keyword-based detection (simple approach)
        happy_keywords = ['happy', 'great', 'wonderful', 'amazing', 'love', 'excited', '!']
        sad_keywords = ['sad', 'sorry', 'unfortunate', 'difficult', 'upset', 'sorry']
        angry_keywords = ['angry', 'frustrated', 'furious', 'hate', 'terrible', '!!']
        calm_keywords = ['relax', 'calm', 'breathe', 'peace', 'gentle', 'slowly']
        surprised_keywords = ['wow', 'amazing', 'incredible', 'shocking', 'unbelievable']
        
        score = {
            'happy': sum(1 for word in happy_keywords if word in text_lower),
            'sad': sum(1 for word in sad_keywords if word in text_lower),
            'angry': sum(1 for word in angry_keywords if word in text_lower),
            'calm': sum(1 for word in calm_keywords if word in text_lower),
            'surprised': sum(1 for word in surprised_keywords if word in text_lower),
        }
        
        # Return emotion with highest score
        emotion = max(score, key=score.get)
        return emotion if score[emotion] > 0 else 'neutral'
    
    def process_response(self, response_text: str, speak: bool = True) -> Tuple[str, str]:
        """
        Process chatbot response with emotion and TTS
        
        Args:
            response_text: The text response from chatbot
            speak: Whether to output audio
            
        Returns:
            Tuple of (response_text, detected_emotion)
        """
        # Detect emotion
        emotion = self.detect_emotion_from_response(response_text)
        
        # Display text response
        print(f"Chatbot: {response_text}")
        print(f"Emotion: {emotion.upper()}")
        
        # Speak with emotion
        if speak:
            self.tts.speak_with_emotion(response_text, emotion=emotion)
        
        # Store in history
        self.conversation_history.append({
            'response': response_text,
            'emotion': emotion
        })
        
        return response_text, emotion
    
    def get_emotion_stats(self) -> dict:
        """Get statistics about emotions used in conversation"""
        if not self.conversation_history:
            return {}
        
        emotions = [item['emotion'] for item in self.conversation_history]
        stats = {}
        
        for emotion in self.tts.list_available_emotions():
            stats[emotion] = emotions.count(emotion)
        
        return stats
    
    def cleanup(self):
        """Clean up resources"""
        self.tts.cleanup()


# ============================================================================
# ADVANCED: Using ML for Emotion Detection
# ============================================================================

class MLEmotionDetector:
    """
    Use transformer models for accurate emotion detection
    Requires: pip install transformers torch
    """
    
    @staticmethod
    def install_dependencies():
        """Install required packages"""
        import subprocess
        subprocess.run([
            "pip", "install", 
            "transformers", "torch", "scikit-learn"
        ], check=True)
    
    @staticmethod
    def detect_emotion_ml(text: str) -> Tuple[str, float]:
        """
        Detect emotion using pre-trained transformer model
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (emotion, confidence_score)
        """
        try:
            from transformers import pipeline
        except ImportError:
            print("Transformers not installed. Run: pip install transformers torch")
            return 'neutral', 0.0
        
        # Use distilbert model for emotion classification
        classifier = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        result = classifier(text)
        emotion = result[0]['label'].lower()
        confidence = result[0]['score']
        
        return emotion, confidence


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize chatbot
    chatbot = EmotionSensitiveChatbot(voice_gender='female')
    
    # Simulate chatbot responses
    test_responses = [
        "That's wonderful news! I'm so happy for you! 😊",
        "I understand you're going through a difficult time. I'm sorry to hear that.",
        "This is incredible! Amazing work! You did it!",
        "Let's take a moment to breathe and relax together. Everything will be okay.",
        "Wow! That's shocking! I didn't expect that at all!"
    ]
    
    print("=== Emotion-Sensitive Chatbot Demo ===\n")
    
    for response in test_responses:
        chatbot.process_response(response, speak=False)  # Set to True for audio
        print("-" * 50)
    
    # Show emotion statistics
    print("\n=== Conversation Emotion Statistics ===")
    stats = chatbot.get_emotion_stats()
    for emotion, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"{emotion}: {count} times")
    
    # Cleanup
    chatbot.cleanup()
