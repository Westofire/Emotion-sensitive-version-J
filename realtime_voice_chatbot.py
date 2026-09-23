import os
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf
import scipy.io.wavfile as wav
import whisper

from chatterbox_emotion_tts import ChatterboxEmotionTTS


# =========================================================
# Ollama Configuration
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/chat"

# Your new, smaller model
MODEL_NAME = "llama3.2:1b"

# Keep the context reasonable for your 8 GB RTX 4060
CONTEXT_SIZE = 2048


# =========================================================
# Emotion Detection
# =========================================================

EMOTION_KEYWORDS = {

    "happy": [
        "happy",
        "great",
        "wonderful",
        "amazing",
        "glad",
        "excited"
    ],

    "sad": [
        "sorry",
        "sad",
        "unfortunate",
        "difficult",
        "upset"
    ],

    "angry": [
        "unacceptable",
        "angry",
        "frustrated",
        "furious",
        "terrible"
    ],

    "calm": [
        "relax",
        "calm",
        "breathe",
        "peace",
        "slowly"
    ],

    "surprised": [
        "wow",
        "seriously",
        "incredible",
        "unbelievable",
        "shocking"
    ],
}


def detect_emotion(text: str) -> str:

    text_lower = text.lower()

    scores = {
        emo: sum(
            1 for word in words
            if word in text_lower
        )
        for emo, words in EMOTION_KEYWORDS.items()
    }

    best = max(scores, key=scores.get)

    return best if scores[best] > 0 else "neutral"


# =========================================================
# Ollama Helpers
# =========================================================

def unload_ollama():

    """
    Ask Ollama to unload the current model from memory.

    This is important because Chatterbox also needs GPU VRAM.
    """

    print("Releasing Ollama model from VRAM...")

    try:

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "keep_alive": 0,
            },
            timeout=30,
        )

        response.raise_for_status()

        print("✓ Ollama model released")

    except requests.RequestException as e:

        print(f"⚠ Could not unload Ollama model: {e}")


def ask_ollama(messages: list) -> str:

    """
    Send conversation history to Ollama.

    Ollama is unloaded after the response so that Chatterbox
    can use the GPU without competing for VRAM.
    """

    payload = {

        "model": MODEL_NAME,

        "messages": messages,

        "stream": False,

        "options": {
            "num_ctx": CONTEXT_SIZE,

            # Allow Ollama to use the GPU.
            "num_gpu": 99,
        },

        # IMPORTANT:
        # Do not retain Llama in VRAM after generating.
        "keep_alive": 0,
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=300,
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


# =========================================================
# Push-to-Talk Recording
# =========================================================

def record_push_to_talk(
    stt_model,
    samplerate: int = 16000,
    temp_filename: str = "temp_pushtotalk.wav"
) -> str:

    user_cmd = input(
        "\n[Press ENTER to START recording | 'q' to exit]: "
    ).strip()

    if user_cmd.lower() in ("q", "quit", "exit"):
        return "__QUIT__"

    audio_frames = []

    def callback(indata, frames, time_info, status):

        if status:
            print(status)

        audio_frames.append(indata.copy())

    with sd.InputStream(
        samplerate=samplerate,
        channels=1,
        callback=callback,
        dtype="float32"
    ):

        input(
            "🔴 Listening... Speak now! "
            "[Press ENTER to STOP and process]: "
        )

    if not audio_frames:
        return ""

    audio_data = np.concatenate(
        audio_frames,
        axis=0
    )

    audio_int16 = (
        audio_data * 32767
    ).astype(np.int16)

    wav.write(
        temp_filename,
        samplerate,
        audio_int16
    )

    print("\n[Transcribing with Whisper Base...]")

    result = stt_model.transcribe(
        temp_filename
    )

    user_text = result["text"].strip()

    if os.path.exists(temp_filename):
        os.remove(temp_filename)

    return user_text


# =========================================================
# Main Chatbot
# =========================================================

def main():

    # -----------------------------------------------------
    # Whisper
    # -----------------------------------------------------

    print("Loading Whisper Base STT model on CPU...")

    # Keep Whisper on CPU so it doesn't consume GPU VRAM.
    stt_model = whisper.load_model(
        "base",
        device="cpu"
    )

    # -----------------------------------------------------
    # Make sure Ollama isn't occupying VRAM
    # -----------------------------------------------------

    unload_ollama()

    # -----------------------------------------------------
    # Chatterbox
    # -----------------------------------------------------

    print("Loading Chatterbox...")

    tts = ChatterboxEmotionTTS()

    # -----------------------------------------------------
    # Audio output
    # -----------------------------------------------------

    output_dir = "audio_outputs"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Conversation state
    # -----------------------------------------------------

    history = []

    turn = 0

    # -----------------------------------------------------
    # Startup message
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("Push-to-Talk Voice Chatbot Ready.")
    print(f" - LLM: {MODEL_NAME}")
    print(f" - Context: {CONTEXT_SIZE}")
    print(" - Whisper: CPU")
    print(" - Chatterbox: GPU")
    print(" - Ollama: released after each response")
    print(" - Press ENTER to start recording.")
    print(" - Press ENTER again to stop recording.")
    print(" - Type 'q' to exit.")
    print("=" * 60)
    print()

    # -----------------------------------------------------
    # Chat loop
    # -----------------------------------------------------

    while True:

        try:

            user_input = record_push_to_talk(
                stt_model
            )

            if user_input == "__QUIT__":

                print("Exiting chatbot...")

                break

            if not user_input:

                print("No audio captured. Try again.")

                continue

            print(f"\nYou: {user_input}")

            # -------------------------------------------------
            # Add user message
            # -------------------------------------------------

            history.append({
                "role": "user",
                "content": user_input
            })

            # -------------------------------------------------
            # Generate LLM response
            # -------------------------------------------------

            print("\n[Generating response with Ollama...]")

            try:

                reply = ask_ollama(
                    history
                )

            except requests.RequestException as e:

                print(
                    f"Ollama error: {e}"
                )

                # Remove failed user message
                history.pop()

                continue

            # -------------------------------------------------
            # Add assistant response
            # -------------------------------------------------

            history.append({
                "role": "assistant",
                "content": reply
            })

            # -------------------------------------------------
            # Detect emotion
            # -------------------------------------------------

            emotion = detect_emotion(
                reply
            )

            audio_path = os.path.join(
                output_dir,
                f"response_{turn}_{emotion}.wav"
            )

            print(
                f"\nBot [{emotion}]: {reply}"
            )

            # -------------------------------------------------
            # Generate TTS
            # -------------------------------------------------

            print(
                "\n[Generating speech with Chatterbox...]"
            )

            try:

                tts.speak_with_emotion(
                    reply,
                    emotion=emotion,
                    output_file=audio_path
                )

                # -------------------------------------------------
                # Play generated audio
                # -------------------------------------------------

                data, samplerate = sf.read(
                    audio_path
                )

                sd.play(
                    data,
                    samplerate
                )

                sd.wait()

            except Exception as e:

                print(
                    f"TTS/audio error: {e}"
                )

            turn += 1

        except (KeyboardInterrupt, EOFError):

            print(
                "\nExiting session..."
            )

            break


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":
    main()