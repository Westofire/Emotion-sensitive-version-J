"""
Emotion-Sensitive Neural TTS using Parler-TTS
Produces genuinely natural speech, with emotion controlled via
natural-language style descriptions (not robotic pitch/rate hacks).

Install:
    pip install git+https://github.com/huggingface/parler-tts.git
    pip install torch soundfile numpy

Requires an NVIDIA GPU for reasonable speed (CPU works but is slow).
"""
import soundfile as sf
import torch
import transformers.pytorch_utils

# Fix for transformers >= 4.45 removing isin_mps_friendly
if not hasattr(transformers.pytorch_utils, "isin_mps_friendly"):
    def isin_mps_friendly(elements, test_elements):
        return torch.isin(elements, test_elements)
    transformers.pytorch_utils.isin_mps_friendly = isin_mps_friendly

# Existing imports continue below
from typing import Optional, Dict
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer


class ParlerEmotionTTS:
    """
    Neural TTS engine where emotion/style is controlled by describing
    the voice in plain English. This is far more natural than
    pitch/rate manipulation on a formant synthesizer.
    """

    # Each emotion maps to a natural-language description of HOW
    # the voice should sound. Tweak these freely -- wording changes
    # actually change the output prosody. These are deliberately
    # theatrical/exaggerated -- stacking intensity words, naming
    # specific vocal behaviors (gasping, trembling, laughing), and
    # using extreme adjectives all push Parler-TTS's prosody further
    # than a single mild adjective does.
    EMOTION_DESCRIPTIONS: Dict[str, str] = {
        "happy": (
            "An extremely cheerful, bubbly female speaker bursts with "
            "over-the-top excitement and joy, her voice bright, warm, and "
            "practically giddy, talking at a fast, energetic pace with big, "
            "exaggerated, sing-song intonation and audible smiling in her "
            "voice, occasionally almost laughing between words, in a quiet "
            "room with very close recording."
        ),
        "sad": (
            "A deeply mournful, heartbroken female speaker talks in a "
            "trembling, weak, breathy voice thick with sorrow, dragging "
            "her words out very slowly and quietly, her tone sinking and "
            "wavering as if on the verge of crying, with long shaky pauses, "
            "in a quiet room with very close recording."
        ),
        "angry": (
            "A furious, seething female speaker nearly shouts in a harsh, "
            "sharp, forceful tone, biting off each word with clipped, "
            "explosive emphasis, her voice rising and cracking with rage, "
            "talking fast and loud with intense clenched-jaw delivery, in "
            "a quiet room with very close recording."
        ),
        "calm": (
            "An extremely relaxed, deeply soothing female speaker talks in "
            "a slow, hushed, velvety tone, drawing out each word smoothly "
            "and evenly with a steady, meditative, almost whispered rhythm, "
            "completely unhurried and tranquil, in a quiet room with very "
            "close recording."
        ),
        "surprised": (
            "An utterly astonished female speaker gasps and talks in a "
            "highly animated, high-pitched tone, her voice leaping upward "
            "with sudden, dramatic emphasis on key words, sounding "
            "breathless and stunned, almost stumbling over her words in "
            "disbelief, in a quiet room with very close recording."
        ),
        "neutral": (
            "A clear, natural female speaker with a normal, even, "
            "conversational tone talks at a moderate pace in a quiet "
            "room with very close recording."
        ),
    }

    # Lighter-touch versions, in case max exaggeration overshoots for a
    # given line of text or you want a "dial" instead of a fixed style.
    EMOTION_DESCRIPTIONS_MILD: Dict[str, str] = {
        "happy": (
            "A cheerful female speaker with a bright, warm, enthusiastic "
            "tone talks at a slightly fast pace with clear expressive "
            "intonation in a quiet room with very close recording."
        ),
        "sad": (
            "A soft, subdued female speaker with a low, gentle, melancholic "
            "tone talks slowly and quietly with a slightly breathy voice "
            "in a quiet room with very close recording."
        ),
        "angry": (
            "An intense female speaker with a sharp, forceful, tense tone "
            "talks quickly and loudly with clipped emphatic delivery in a "
            "quiet room with very close recording."
        ),
        "calm": (
            "A relaxed, soothing female speaker with a warm, even, gentle "
            "tone talks slowly and smoothly with a steady, reassuring "
            "rhythm in a quiet room with very close recording."
        ),
        "surprised": (
            "An animated female speaker with a bright, high-energy tone "
            "talks with sudden emphasis and rising pitch, sounding "
            "amazed, in a quiet room with very close recording."
        ),
        "neutral": (
            "A clear, natural female speaker with a normal, even, "
            "conversational tone talks at a moderate pace in a quiet "
            "room with very close recording."
        ),
    }

    def __init__(
        self,
        model_name: str = "parler-tts/parler-tts-mini-v1",
        device: Optional[str] = None,
    ):
        """
        Args:
            model_name: 'parler-tts/parler-tts-mini-v1' (faster) or
                        'parler-tts/parler-tts-large-v1' (higher quality,
                        needs more VRAM, ~10GB+)
            device: 'cuda', 'cpu', or None to auto-detect
        """
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"Loading Parler-TTS on {self.device} (first run downloads the model)...")

        self.model = ParlerTTSForConditionalGeneration.from_pretrained(
            model_name
        ).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.description_tokenizer = AutoTokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path
        )
        print("✓ Model loaded")

    def speak_with_emotion(
        self,
        text: str,
        emotion: str = "neutral",
        custom_description: Optional[str] = None,
        output_file: str = "output.wav",
        intensity: str = "exaggerated",
    ) -> str:
        """
        Generate natural speech with the given emotion.

        Args:
            text: what to say
            emotion: one of EMOTION_DESCRIPTIONS keys
            custom_description: override the built-in style prompt entirely
            output_file: path to save the .wav file
            intensity: "exaggerated" (default, theatrical/over-the-top) or
                       "mild" (closer to naturalistic delivery)

        Returns:
            path to the saved audio file
        """
        description_bank = (
            self.EMOTION_DESCRIPTIONS
            if intensity == "exaggerated"
            else self.EMOTION_DESCRIPTIONS_MILD
        )
        description = custom_description or description_bank.get(
            emotion.lower(), description_bank["neutral"]
        )

        input_ids = self.description_tokenizer(
            description, return_tensors="pt"
        ).input_ids.to(self.device)
        prompt_input_ids = self.tokenizer(
            text, return_tensors="pt"
        ).input_ids.to(self.device)

        generation = self.model.generate(
            input_ids=input_ids, prompt_input_ids=prompt_input_ids
        )
        audio_arr = generation.cpu().numpy().squeeze()

        sf.write(output_file, audio_arr, self.model.config.sampling_rate)
        print(f"✓ Saved: {output_file}  (emotion: {emotion})")
        return output_file

    def list_available_emotions(self):
        return list(self.EMOTION_DESCRIPTIONS.keys())


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    tts = ParlerEmotionTTS(model_name="parler-tts/parler-tts-mini-v1")

    responses = [
        ("happy", "That's wonderful news! I'm so glad it worked out!"),
        ("sad", "I'm really sorry you're going through that."),
        ("angry", "This is completely unacceptable, we need to fix it now."),
        ("calm", "Let's take a moment. Everything is going to be fine."),
        ("surprised", "Wait, seriously? I did not see that coming!"),
    ]

    for emotion, text in responses:
        tts.speak_with_emotion(
            text, emotion=emotion, output_file=f"demo_{emotion}.wav"
        )

