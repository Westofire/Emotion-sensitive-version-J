"""
Simple voice chatbot:
- Ollama (Qwen 2.5 7B Instruct) generates the text response
- Chatterbox speaks it back with matching emotion

Ollama model:
    qwen2.5-7b-4060

This model is configured for:
    - 2048 token context
    - 100% GPU on an 8 GB RTX 4060

Requirements:
    pip install requests soundfile sounddevice chatterbox-tts

Run:
    ollama serve
    python ollama_voice_chatbot.py
"""

import os
import requests
import soundfile as sf
import sounddevice as sd
from chatterbox_emotion_tts import ChatterboxEmotionTTS


# ---------------------------------------------------------
# Ollama configuration
# ---------------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/chat"

# IMPORTANT:
# Use the custom model we created for your RTX 4060.
MODEL_NAME = "qwen2.5-7b-4060"

# Keep the context at 2048 so the model remains entirely
# on the RTX 4060 instead of being split between CPU/GPU.
CONTEXT_SIZE = 2048


# ---------------------------------------------------------
# Emotion detection
# ---------------------------------------------------------

EMOTION_KEYWORDS = {
    "happy": [
        "happy",
        "great",
        "wonderful",
        "amazing",
        "glad",
        "excited",
    ],

    "sad": [
        "sorry",
        "sad",
        "unfortunate",
        "difficult",
        "upset",
    ],

    "angry": [
        "unacceptable",
        "angry",
        "frustrated",
        "furious",
        "terrible",
    ],

    "calm": [
        "relax",
        "calm",
        "breathe",
        "peace",
        "slowly",
    ],

    "surprised": [
        "wow",
        "seriously",
        "incredible",
        "unbelievable",
        "shocking",
    ],
}


def detect_emotion(text: str) -> str:
    """Detect the dominant emotion using simple keywords."""

    text_lower = text.lower()

    scores = {
        emotion: sum(
            1 for word in words
            if word in text_lower
        )
        for emotion, words in EMOTION_KEYWORDS.items()
    }

    best_emotion = max(scores, key=scores.get)

    if scores[best_emotion] > 0:
        return best_emotion

    return "neutral"


# ---------------------------------------------------------
# Ollama
# ---------------------------------------------------------

def ask_ollama(messages: list) -> str:
    """Send conversation history to Ollama and get a response."""

    payload = {
        "model": MODEL_NAME,

        "messages": messages,

        "stream": False,

        # Explicitly enforce the 2048-token context.
        "options": {
            "num_ctx": CONTEXT_SIZE,
        },

        # Keep the model loaded between turns.
        "keep_alive": 0,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]


# ---------------------------------------------------------
# Main chatbot
# ---------------------------------------------------------

def main():

    print("Loading Chatterbox...")

    tts = ChatterboxEmotionTTS()

    output_dir = "audio_outputs"
    os.makedirs(output_dir, exist_ok=True)

    history = []

    turn = 0

    print()
    print("=" * 60)
    print("Voice chatbot ready.")
    print(f"Ollama model : {MODEL_NAME}")
    print(f"Context      : {CONTEXT_SIZE}")
    print("Type 'quit' or 'exit' to stop.")
    print("=" * 60)
    print()

    while True:

        try:
            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Add user message
        history.append({
            "role": "user",
            "content": user_input,
        })

        try:
            # -------------------------------------------------
            # Generate response
            # -------------------------------------------------

            reply = ask_ollama(history)

        except requests.RequestException as e:

            print(f"\nOllama error: {e}\n")

            # Remove the failed user message so that the
            # conversation history doesn't become corrupted.
            history.pop()

            continue

        # Add assistant response to conversation history
        history.append({
            "role": "assistant",
            "content": reply,
        })

        # -------------------------------------------------
        # Detect emotion
        # -------------------------------------------------

        emotion = detect_emotion(reply)

        audio_path = os.path.join(
            output_dir,
            f"response_{turn}_{emotion}.wav"
        )

        print()
        print(f"Bot [{emotion}]: {reply}")
        print()

        # -------------------------------------------------
        # Generate speech
        # -------------------------------------------------

        try:

            tts.speak_with_emotion(
                reply,
                emotion=emotion,
                output_file=audio_path,
            )

        except Exception as e:

            print(f"TTS error: {e}")
            turn += 1
            continue

        # -------------------------------------------------
        # Play audio
        # -------------------------------------------------

        try:

            data, samplerate = sf.read(audio_path)

            sd.play(data, samplerate)

            # Wait until playback finishes before accepting
            # the next message.
            sd.wait()

        except Exception as e:

            print(f"Audio playback error: {e}")

        turn += 1


if __name__ == "__main__":
    main()
