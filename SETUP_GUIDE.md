# Emotion-Sensitive Text-to-Speech Setup Guide

## Quick Start

### 1. Installation

**Basic setup (pyttsx3 - recommended for beginners):**

```bash
pip install pyttsx3
```

**For Linux users:**
```bash
sudo apt-get install espeak ffmpeg libespeak1
pip install pyttsx3
```

**For macOS:**
```bash
brew install espeak
pip install pyttsx3
```

### 2. Basic Usage

```python
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
```

---

## Available Emotions

| Emotion | Rate | Volume | Pitch | Use Case |
|---------|------|--------|-------|----------|
| **HAPPY** | 160 (fast) | 1.0 | 1.4 (high) | Positive, enthusiastic responses |
| **SAD** | 100 (slow) | 0.7 | 0.8 (low) | Empathetic, understanding responses |
| **ANGRY** | 180 (very fast) | 1.0 | 1.2 | Frustrated, emphatic statements |
| **CALM** | 110 (slow) | 0.9 | 0.9 | Soothing, meditative responses |
| **SURPRISED** | 140 (medium) | 1.0 | 1.5 (very high) | Unexpected, exciting statements |
| **NEUTRAL** | 125 (normal) | 1.0 | 1.0 | Default, informational responses |

---

## Architecture

```
┌─────────────────────────────────────────┐
│    Chatbot Response Generation          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    Emotion Detection Module             │
│  (Keyword-based or ML-based)            │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    Emotion-Sensitive TTS                │
│  (Apply pitch, speed, volume params)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│    Audio Output / File Save             │
│  (Speaker or MP3/WAV file)              │
└─────────────────────────────────────────┘
```

---

## Advanced Setup: ML-Based Emotion Detection

For more accurate emotion detection, use transformer models:

### Installation

```bash
pip install transformers torch scikit-learn
```

### Usage

```python
from integration_example import MLEmotionDetector

# Detect emotion
emotion, confidence = MLEmotionDetector.detect_emotion_ml(
    "I'm so happy and excited!"
)
print(f"Emotion: {emotion} (Confidence: {confidence:.2f})")
```

---

## Alternative: Piper TTS (Advanced)

For superior pitch control and more natural voices:

```bash
pip install piper-tts
```

**Advantages:**
- Direct pitch control (not just workaround)
- More realistic voices
- Offline operation
- Lower latency

**Disadvantage:**
- Requires more setup

---

## Comparison: pyttsx3 vs Piper vs Cloud APIs

| Feature | pyttsx3 | Piper | Google TTS | AWS Polly |
|---------|---------|-------|-----------|-----------|
| **Offline** | ✓ | ✓ | ✗ | ✗ |
| **Speed** | Fast | Medium | Slow | Slow |
| **Pitch Control** | Limited | Good | Excellent | Excellent |
| **Free** | ✓ | ✓ | Paid | Paid |
| **Setup Complexity** | Easy | Medium | Easy | Medium |
| **Quality** | Good | Excellent | Excellent | Excellent |
| **Emotion Support** | Manual | Manual | Built-in | Built-in |

**Recommendation for your project:** Start with **pyttsx3** (simplicity), upgrade to **Piper** if better quality is needed.

---

## Complete Integration Example

```python
from integration_example import EmotionSensitiveChatbot

# Create chatbot
bot = EmotionSensitiveChatbot(voice_gender='female')

# Process responses with emotion
bot.process_response(
    "That's amazing! I'm so proud of you!",
    speak=True
)

# Get emotion statistics
stats = bot.get_emotion_stats()
print(f"Used emotions: {stats}")

# Cleanup
bot.cleanup()
```

---

## Troubleshooting

### Issue: No audio output
**Solution:** 
- Check speakers are on
- Verify system audio settings
- On Linux, ensure `espeak` is installed

### Issue: `ModuleNotFoundError: No module named 'pyttsx3'`
**Solution:**
```bash
pip install --upgrade pyttsx3
```

### Issue: Poor pitch/speed control
**Solution:** Upgrade to Piper:
```bash
pip install piper-tts
```

### Issue: Very distorted audio
**Solution:**
- Reduce `volume` parameter (0.5-0.9)
- Use more moderate `rate` values (80-160)
- Try different voice with `voice_gender` parameter

---

## Project Integration Checklist

- [ ] Install pyttsx3: `pip install pyttsx3`
- [ ] Copy `emotion_tts.py` to your project
- [ ] Copy `integration_example.py` to your project
- [ ] Import `EmotionTTS` in your chatbot
- [ ] Add emotion detection logic
- [ ] Test with different emotions
- [ ] (Optional) Switch to Piper for better quality
- [ ] (Optional) Add ML-based emotion detection

---

## Key Parameters to Adjust

```python
# You can customize emotion parameters:
Emotion.HAPPY = {
    'rate': 160,      # 50-200 (words per minute)
    'volume': 1.0,    # 0.0-1.0
    'pitch': 1.4,     # Piper: 0.5-2.0, pyttsx3: workaround via rate
}
```

Experiment with these values to match your desired tone!

---

## Next Steps

1. **Test locally** with the provided examples
2. **Integrate** with your chatbot's response generation
3. **Tune emotions** for your specific use cases
4. **Add ML detection** for better accuracy
5. **Optimize audio quality** with parameter tweaking

Good luck with your project! 🎉
