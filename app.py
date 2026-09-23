import os
import gradio as gr
from parler_emotion_tts import ParlerEmotionTTS

# Initialize the Parler-TTS model
tts_engine = ParlerEmotionTTS(model_name="parler-tts/parler-tts-mini-v1")

def synthesize_speech(text: str, emotion: str, intensity: str, custom_prompt: str):
    if not text.strip():
        return None, "Error: Please enter text to generate speech."

    # Use custom prompt if provided; otherwise fallback to selected emotion/intensity
    override_description = custom_prompt.strip() if custom_prompt.strip() else None
    
    output_filename = f"output_{emotion}_{intensity}.wav"
    
    # Generate audio file
    tts_engine.speak_with_emotion(
        text=text,
        emotion=emotion,
        custom_description=override_description,
        output_file=output_filename,
        intensity=intensity
    )
    
    status_msg = f"Successfully generated speech with '{emotion}' emotion ({intensity} intensity)."
    return output_filename, status_msg

# Build the Gradio UI
with gr.Blocks(title="Parler-TTS Emotion Generator") as app:
    gr.Markdown("## Parler-TTS Interactive Emotion Generator")
    gr.Markdown("Type a message, select an emotion, and generate speech.")

    with gr.Row():
        with gr.Column(scale=1):
            text_input = gr.Textbox(
                lines=4,
                placeholder="Type the text you want spoken here...",
                label="Speech Text",
                value="That's wonderful news! I'm so glad it worked out!"
            )
            
            emotion_dropdown = gr.Dropdown(
                choices=["happy", "sad", "angry", "calm", "surprised", "neutral"],
                value="happy",
                label="Select Emotion"
            )
            
            intensity_radio = gr.Radio(
                choices=["exaggerated", "mild"],
                value="exaggerated",
                label="Emotion Intensity"
            )
            
            custom_prompt_input = gr.Textbox(
                lines=2,
                placeholder="Optional: Overrides emotion with a custom voice prompt...",
                label="Custom Style Prompt (Optional)"
            )
            
            generate_btn = gr.Button("Generate Speech", variant="primary")

        with gr.Column(scale=1):
            audio_output = gr.Audio(label="Generated Audio Output", type="filepath")
            status_output = gr.Textbox(label="Status", interactive=False)

    # Trigger generation
    generate_btn.click(
        fn=synthesize_speech,
        inputs=[text_input, emotion_dropdown, intensity_radio, custom_prompt_input],
        outputs=[audio_output, status_output]
    )

if __name__ == "__main__":
    app.launch(share=False)