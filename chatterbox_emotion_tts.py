"""
Emotion-flavored TTS using Chatterbox (Resemble AI, MIT license).

Chatterbox doesn't take natural-language style prompts either, but it
does expose two real knobs that map naturally onto "emotion":
  - exaggeration: how dramatic/expressive the delivery is
  - cfg_weight:   lower values = slower, more deliberate pacing

This is a drop-in replacement for KokoroEmotionTTS/ParlerEmotionTTS:
same speak_with_emotion() signature, so the chatbot script barely changes.

Install:
    pip install chatterbox-tts

Requires an NVIDIA GPU for reasonable speed (CPU works but is slow).
"""

import torchaudio as ta
from typing import Dict, Tuple
from chatterbox.tts import ChatterboxTTS


class ChatterboxEmotionTTS:

    # emotion -> (exaggeration, cfg_weight)
    EMOTION_SETTINGS: Dict[str, Tuple[float, float]] = {
        "happy":     (0.7, 0.4),
        "sad":       (0.6, 0.45),
        "angry":     (0.8, 0.3),
        "calm":      (0.3, 0.5),
        "surprised": (0.75, 0.35),
        "neutral":   (0.5, 0.5),
    }

    def __init__(self, device: str = "cuda"):
        print(f"Loading Chatterbox on {device} (first run downloads the model)...")
        self.model = ChatterboxTTS.from_pretrained(device=device)
        print("✓ Chatterbox loaded")

    def speak_with_emotion(
        self,
        text: str,
        emotion: str = "neutral",
        output_file: str = "output.wav",
        audio_prompt_path: str = None,  # optional: clone a specific voice
        **kwargs,  # swallows old Parler/Kokoro-only args
    ) -> str:
        exaggeration, cfg_weight = self.EMOTION_SETTINGS.get(
            emotion.lower(), self.EMOTION_SETTINGS["neutral"]
        )

        wav = self.model.generate(
            text,
            audio_prompt_path=audio_prompt_path,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )

        ta.save(output_file, wav, self.model.sr)
        print(f"✓ Saved: {output_file}  (emotion: {emotion})")
        return output_file

    def list_available_emotions(self):
        return list(self.EMOTION_SETTINGS.keys())


if __name__ == "__main__":
    tts = ChatterboxEmotionTTS()
    for emotion in tts.list_available_emotions():
        tts.speak_with_emotion(
            f"This is a test of the {emotion} emotion.",
            emotion=emotion,
            output_file=f"demo_{emotion}.wav",
        )
