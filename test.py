from emotion_tts import EmotionTTS

# Initialize
tts = EmotionTTS(voice_gender='female')

# Speak with emotion
tts.speak_with_emotion(
    text="I'm so excited to help you!",
    emotion='happy'
)

# Cleanup
tts.cleanup()