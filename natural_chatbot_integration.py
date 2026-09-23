"""
Emotion-Sensitive Chatbot integrated with Parler-TTS
(natural neural speech instead of robotic pyttsx3)
"""

from parler_emotion_tts import ParlerEmotionTTS
from typing import Tuple
import os


class NaturalEmotionChatbot:
    def __init__(self, model_name: str = "parler-tts/parler-tts-mini-v1"):
        self.tts = ParlerEmotionTTS(model_name=model_name)
        self.conversation_history = []
        self.output_dir = "audio_outputs"
        os.makedirs(self.output_dir, exist_ok=True)

    def detect_emotion_from_response(self, text: str) -> str:
        """
        Simple keyword-based detection. Swap this for a proper
        classifier (e.g. a fine-tuned DistilRoBERTa emotion model)
        for your final submission -- see note below.
        """
        text_lower = text.lower()

        keywords = {
            "happy": ["happy", "great", "wonderful", "amazing", "glad", "excited"],
            "sad": ["sorry", "sad", "unfortunate", "difficult", "upset"],
            "angry": ["unacceptable", "angry", "frustrated", "furious", "terrible"],
            "calm": ["relax", "calm", "breathe", "peace", "slowly"],
            "surprised": ["wow", "seriously", "incredible", "unbelievable", "shocking"],
        }

        scores = {
            emo: sum(1 for w in words if w in text_lower)
            for emo, words in keywords.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "neutral"

    def process_response(self, response_text: str, turn_id: int) -> Tuple[str, str, str]:
        emotion = self.detect_emotion_from_response(response_text)
        output_path = os.path.join(self.output_dir, f"response_{turn_id}_{emotion}.wav")

        self.tts.speak_with_emotion(response_text, emotion=emotion, output_file=output_path)

        self.conversation_history.append(
            {"text": response_text, "emotion": emotion, "audio": output_path}
        )
        return response_text, emotion, output_path


if __name__ == "__main__":
    bot = NaturalEmotionChatbot()

    test_responses = [
        "That's wonderful news! I'm so happy for you!",
        "I'm really sorry to hear you're going through that.",
        "This is completely unacceptable, we need to fix it immediately.",
        "Let's take a moment to breathe. Everything will be okay.",
        "Wait, seriously? I didn't expect that at all!",
    ]

    for i, resp in enumerate(test_responses):
        text, emotion, audio_path = bot.process_response(resp, turn_id=i)
        print(f"[{emotion.upper()}] {text} -> {audio_path}")
