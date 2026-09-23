import os
import time
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf
import scipy.io.wavfile as wav
import whisper
import torch
import transformers.pytorch_utils
from typing import Optional, Dict
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

# ---------------------------------------------------------
# Transformers Compatibility Patch
# ---------------------------------------------------------
if not hasattr(transformers.pytorch_utils, "isin_mps_friendly"):
    def isin_mps_friendly(elements, test_elements):
        return torch.isin(elements, test_elements)
    transformers.pytorch_utils.isin_mps_friendly = isin_mps_friendly


# ---------------------------------------------------------
# Parler-TTS Engine
# ---------------------------------------------------------
class ParlerEmotionTTS:
    EMOTION_DESCRIPTIONS: Dict[str, str] = {
        "happy": (
            "An extremely cheerful, bubbly female speaker bursts with over-the-top excitement "
            "and joy, her voice bright, warm, and practically giddy, talking at a fast, energetic "
            "pace with big, exaggerated intonation in a quiet room with very close recording."
        ),
        "sad": (
            "A deeply mournful, heartbroken female speaker talks in a trembling, weak, breathy voice "
            "thick with sorrow, dragging her words out very slowly and quietly in a quiet room."
        ),
        "angry": (
            "A furious, seething female speaker nearly shouts in a harsh, sharp, forceful tone, "
            "biting off each word with clipped, explosive emphasis in a quiet room."
        ),
        "calm": (
            "An extremely relaxed, deeply soothing female speaker talks in a slow, hushed, velvety tone, "
            "drawing out each word smoothly and evenly in a quiet room with very close recording."
        ),
        "surprised": (
            "An utterly astonished female speaker gasps and talks in a highly animated, high-pitched tone, "
            "her voice leaping upward with sudden emphasis in a quiet room."
        ),
        "neutral": (
            "A clear, natural female speaker with a normal, even, conversational tone talks at a "
            "moderate pace in a quiet room with very close recording."
        ),
    }

    def __init__(self, model_name: str = "parler-tts/parler-tts-mini-v1", device: Optional[str] = None):
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        print(f"Loading Parler-TTS on {self.device}...")
        self.model = ParlerTTSForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.description_tokenizer = AutoTokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path
        )
        print("✓ Parler-TTS loaded")

    def speak_with_emotion(self, text: str, emotion: str = "neutral", output_file: str = "output.wav") -> str:
        description = self.EMOTION_DESCRIPTIONS.get(emotion.lower(), self.EMOTION_DESCRIPTIONS["neutral"])
        
        input_ids = self.description_tokenizer(description, return_tensors="pt").input_ids.to(self.device)
        prompt_input_ids = self.tokenizer(text, return_tensors="pt").input_ids.to(self.device)

        generation = self.model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
        audio_arr = generation.cpu().numpy().squeeze()

        sf.write(output_file, audio_arr, self.model.config.sampling_rate)
        return output_file


# ---------------------------------------------------------
# Ollama Configuration & Emotion Detection
# ---------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-7b-4060"
CONTEXT_SIZE = 2048

EMOTION_KEYWORDS = {
    "happy": ["happy", "great", "wonderful", "amazing", "glad", "excited"],
    "sad": ["sorry", "sad", "unfortunate", "difficult", "upset"],
    "angry": ["unacceptable", "angry", "frustrated", "furious", "terrible"],
    "calm": ["relax", "calm", "breathe", "peace", "slowly"],
    "surprised": ["wow", "seriously", "incredible", "unbelievable", "shocking"],
}

def detect_emotion(text: str) -> str:
    text_lower = text.lower()
    scores = {emo: sum(1 for w in words if w in text_lower) for emo, words in EMOTION_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "neutral"

def ask_ollama(messages: list) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": CONTEXT_SIZE},
        "keep_alive": 0,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()["message"]["content"]


# ---------------------------------------------------------
# Push-to-Talk Recording Function
# ---------------------------------------------------------
def record_push_to_talk(
    stt_model,
    samplerate: int = 16000,
    temp_filename: str = "temp_pushtotalk.wav"
) -> str:
    # 1. Wait for user to trigger start
    user_cmd = input("\n[Press ENTER to START recording | 'q' to exit]: ").strip()
    if user_cmd.lower() in ("q", "quit", "exit"):
        return "__QUIT__"

    audio_frames = []

    def callback(indata, frames, time_info, status):
        audio_frames.append(indata.copy())

    # 2. Open continuous audio recording stream
    with sd.InputStream(samplerate=samplerate, channels=1, callback=callback, dtype='float32'):
        # 3. Wait for user to trigger stop
        input("🔴 Listening... Speak now! [Press ENTER to STOP and process]: ")

    if not audio_frames:
        return ""

    # 4. Save and transcribe recorded audio
    audio_data = np.concatenate(audio_frames, axis=0)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    wav.write(temp_filename, samplerate, audio_int16)

    print("\n[Transcribing with Whisper Base...]")
    result = stt_model.transcribe(temp_filename)
    user_text = result["text"].strip()

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return user_text


# ---------------------------------------------------------
# Main Chatbot Loop
# ---------------------------------------------------------
def main():
    print("Loading Whisper Base STT model...")
    stt_model = whisper.load_model("base")

    tts = ParlerEmotionTTS(model_name="parler-tts/parler-tts-mini-v1")

    output_dir = "audio_outputs"
    os.makedirs(output_dir, exist_ok=True)

    history = []
    turn = 0

    print("\n" + "=" * 60)
    print("Push-to-Talk Voice Chatbot Ready.")
    print(" - Press ENTER to start recording.")
    print(" - Press ENTER again to stop and get an answer.")
    print(" - Type 'q' to exit.")
    print("=" * 60 + "\n")

    while True:
        try:
            # 1. Push to talk input
            user_input = record_push_to_talk(stt_model)

            if user_input == "__QUIT__":
                print("Exiting chatbot...")
                break

            if not user_input:
                print("No audio captured. Try again.")
                continue

            print(f"\nYou: {user_input}")

            # 2. Query Ollama
            history.append({"role": "user", "content": user_input})
            try:
                reply = ask_ollama(history)
            except requests.RequestException as e:
                print(f"Ollama error: {e}")
                history.pop()
                continue

            history.append({"role": "assistant", "content": reply})

            # 3. Detect emotion and synthesize response
            emotion = detect_emotion(reply)
            audio_path = os.path.join(output_dir, f"response_{turn}_{emotion}.wav")
            print(f"\nBot [{emotion}]: {reply}")

            try:
                tts.speak_with_emotion(reply, emotion=emotion, output_file=audio_path)
                data, samplerate = sf.read(audio_path)
                sd.play(data, samplerate)
                sd.wait()
            except Exception as e:
                print(f"Audio playback error: {e}")

            turn += 1

        except (KeyboardInterrupt, EOFError):
            print("\nExiting session...")
            break


if __name__ == "__main__":
    main()  