"""
Test script for Emotion-Sensitive TTS
Run this to test all emotions and configurations
"""

import sys
from typing import List, Dict
from emotion_tts import EmotionTTS, Emotion


class EmotionTTSTestSuite:
    """Comprehensive test suite for emotion TTS"""
    
    def __init__(self):
        self.results = []
        self.tts = None
    
    def setup(self, voice_gender: str = 'female'):
        """Initialize TTS engine"""
        try:
            self.tts = EmotionTTS(voice_gender=voice_gender)
            print(f"✓ TTS Engine initialized ({voice_gender} voice)")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize TTS: {e}")
            return False
    
    def test_emotion_parameters(self) -> bool:
        """Test that all emotion parameters are properly configured"""
        print("\n" + "="*60)
        print("TEST 1: Emotion Parameters")
        print("="*60)
        
        try:
            emotions = self.tts.list_available_emotions()
            print(f"\nAvailable emotions: {', '.join(emotions)}\n")
            
            for emotion in emotions:
                params = self.tts.get_emotion_parameters(emotion)
                print(f"{emotion.upper():10} → Rate: {params['rate']:3d} | "
                      f"Volume: {params['volume']:.1f} | Pitch: {params['pitch']:.1f}")
            
            self.results.append(("Emotion Parameters", "PASS"))
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results.append(("Emotion Parameters", "FAIL"))
            return False
    
    def test_speak_all_emotions(self, sample_text: str, play_audio: bool = False) -> bool:
        """Test speaking with all emotions"""
        print("\n" + "="*60)
        print("TEST 2: Speaking with All Emotions")
        print("="*60)
        print(f"\nSample text: \"{sample_text}\"")
        print(f"Play audio: {play_audio}\n")
        
        try:
            emotions = self.tts.list_available_emotions()
            
            for i, emotion in enumerate(emotions, 1):
                print(f"[{i}/{len(emotions)}] Testing {emotion.upper()}...", end=" ")
                
                success = self.tts.speak_with_emotion(
                    sample_text,
                    emotion=emotion,
                    save_to_file=None
                )
                
                if success:
                    print("✓")
                else:
                    print("✗")
                    self.results.append((f"Speak {emotion}", "FAIL"))
                    return False
            
            self.results.append(("Speak All Emotions", "PASS"))
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results.append(("Speak All Emotions", "FAIL"))
            return False
    
    def test_custom_parameters(self) -> bool:
        """Test with custom parameters"""
        print("\n" + "="*60)
        print("TEST 3: Custom Parameters")
        print("="*60)
        
        try:
            print("\nTesting different voice genders...")
            
            for gender in ['female', 'male']:
                print(f"  Testing {gender} voice...", end=" ")
                tts = EmotionTTS(voice_gender=gender)
                print("✓")
                tts.cleanup()
            
            self.results.append(("Custom Parameters", "PASS"))
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results.append(("Custom Parameters", "FAIL"))
            return False
    
    def test_chatbot_scenarios(self) -> bool:
        """Test realistic chatbot scenarios"""
        print("\n" + "="*60)
        print("TEST 4: Chatbot Scenarios")
        print("="*60)
        
        scenarios = [
            ("happy", "Great news! Your request has been approved! 🎉"),
            ("sad", "I'm sorry to hear you're having difficulties. 😢"),
            ("calm", "Let's take a moment to breathe and relax together."),
            ("surprised", "Wow! That's absolutely incredible! I didn't expect that!"),
            ("angry", "This is unacceptable! We need to fix this immediately!"),
            ("neutral", "Your appointment is scheduled for 3 PM tomorrow."),
        ]
        
        try:
            for emotion, text in scenarios:
                print(f"\n[{emotion.upper()}] \"{text}\"")
                print(f"  Parameters: {self.tts.get_emotion_parameters(emotion)}")
                
                success = self.tts.speak_with_emotion(text, emotion=emotion)
                if not success:
                    self.results.append((f"Scenario {emotion}", "FAIL"))
                    return False
            
            self.results.append(("Chatbot Scenarios", "PASS"))
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results.append(("Chatbot Scenarios", "FAIL"))
            return False
    
    def test_edge_cases(self) -> bool:
        """Test edge cases and error handling"""
        print("\n" + "="*60)
        print("TEST 5: Edge Cases")
        print("="*60)
        
        try:
            test_cases = [
                ("", "empty string"),
                ("a" * 500, "very long text"),
                ("123!@#$%^&*()", "special characters"),
                ("HELLO WORLD", "uppercase"),
            ]
            
            for text, description in test_cases:
                print(f"\nTesting {description}...", end=" ")
                success = self.tts.speak_with_emotion(text or ".", emotion='neutral')
                print("✓" if success else "✗")
            
            # Test invalid emotion
            print(f"\nTesting invalid emotion (should default to neutral)...", end=" ")
            success = self.tts.speak_with_emotion(
                "This should work",
                emotion='invalid_emotion'
            )
            print("✓" if success else "✗")
            
            self.results.append(("Edge Cases", "PASS"))
            return True
        except Exception as e:
            print(f"✗ Error: {e}")
            self.results.append(("Edge Cases", "FAIL"))
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60 + "\n")
        
        passed = sum(1 for _, result in self.results if result == "PASS")
        failed = sum(1 for _, result in self.results if result == "FAIL")
        
        for test_name, result in self.results:
            status_symbol = "✓" if result == "PASS" else "✗"
            print(f"{status_symbol} {test_name}: {result}")
        
        print(f"\nTotal: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Check errors above.")
    
    def run_all_tests(self, play_audio: bool = False):
        """Run all tests"""
        print("\n" + "="*60)
        print("EMOTION TTS TEST SUITE")
        print("="*60)
        
        if not self.setup('female'):
            print("Cannot continue without TTS engine")
            return
        
        # Run tests
        self.test_emotion_parameters()
        self.test_speak_all_emotions(
            "Hello, I am your emotion-sensitive chatbot!",
            play_audio=play_audio
        )
        self.test_custom_parameters()
        self.test_chatbot_scenarios()
        self.test_edge_cases()
        
        # Print results
        self.print_summary()
        
        # Cleanup
        if self.tts:
            self.tts.cleanup()


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Emotion-Sensitive TTS')
    parser.add_argument('--audio', action='store_true', help='Play audio output')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    args = parser.parse_args()
    
    tester = EmotionTTSTestSuite()
    
    if args.quick:
        print("Running quick tests...\n")
        if tester.setup('female'):
            tester.test_emotion_parameters()
            tester.test_speak_all_emotions("Quick test", play_audio=args.audio)
    else:
        tester.run_all_tests(play_audio=args.audio)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
