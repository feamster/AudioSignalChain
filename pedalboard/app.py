# app.py
import gradio as gr
import numpy as np
import os
import time
import sounddevice as sd
from pedalboard import (
    Chorus, Delay, Distortion, Gain, Reverb,
    Phaser, Compressor, Limiter, LadderFilter,
    Bitcrush, PitchShift
)
from effects_processor import EffectsProcessor
from effects_presets import get_effect_presets, get_individual_effects

# Create the effects processor
processor = EffectsProcessor(sample_rate=44100, block_size=512, channels=1)
presets = get_effect_presets()
individual_effects = get_individual_effects()

# Setup temp directory for recordings
TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)


def apply_preset(preset_name):
    """Apply a preset to the effects chain"""
    if not preset_name or preset_name == "None":
        processor.clear_effects()
        return f"Cleared all effects"

    if preset_name in presets:
        processor.clear_effects()
        preset_board = presets[preset_name]()
        for effect in preset_board:
            processor.add_effect(effect)
        return f"Applied {preset_name} preset with {len(preset_board)} effects"

    return f"Preset {preset_name} not found"


def add_individual_effect(effect_name):
    """Add an individual effect to the chain"""
    if not effect_name or effect_name == "None":
        return "No effect selected"

    if effect_name in individual_effects:
        effect = individual_effects[effect_name]()
        index = processor.add_effect(effect)
        return f"Added {effect_name} at position {index}"

    return f"Effect {effect_name} not found"


def update_effect_param(effect_index, param_name, value):
    """Update a parameter of an effect"""
    if effect_index is None:
        return "No effect selected"

    try:
        index = int(effect_index)
        success = processor.update_effect_parameter(index, param_name, value)
        if success:
            return f"Updated {param_name} to {value} for effect at position {index}"
        else:
            return f"Failed to update parameter. Check if effect exists and has this parameter."
    except ValueError:
        return "Invalid effect index"


def get_current_effects():
    """Get the current effects chain as a string"""
    effects = processor.get_effects()
    if not effects:
        return "No effects in the chain"

    result = "Current Effects Chain:\n"
    for i, effect in enumerate(effects):
        effect_type = type(effect).__name__
        params = {name: getattr(effect, name) for name in dir(effect)
                  if not name.startswith('_') and not callable(getattr(effect, name))}
        result += f"{i}: {effect_type} - {params}\n"

    return result


def start_processing():
    """Start the audio processing"""
    if not processor.is_running:
        processor.start()
        return "Audio processing started"
    return "Audio processing already running"


def stop_processing():
    """Stop the audio processing"""
    if processor.is_running:
        processor.stop()
        return "Audio processing stopped"
    return "Audio processing already stopped"


def record_audio(seconds):
    """Record audio for the specified number of seconds"""
    if seconds <= 0:
        return None, "Recording duration must be positive"

    # Setup recording
    sample_rate = 44100
    channels = 1
    recording = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=channels, dtype='float32')
    sd.wait()  # Wait until recording is finished

    # Save the recording to a file
    timestamp = int(time.time())
    filename = os.path.join(TEMP_DIR, f"recording_{timestamp}.wav")
    import soundfile as sf
    sf.write(filename, recording, sample_rate)

    return filename, f"Recorded {seconds} seconds of audio"


def process_audio_file(input_file, effect_preset=None):
    """Process an audio file through the effects chain"""
    if input_file is None:
        return None, "No input file provided"

    # Apply preset if specified
    if effect_preset and effect_preset != "None":
        apply_preset(effect_preset)

    # Process the file
    timestamp = int(time.time())
    output_file = os.path.join(TEMP_DIR, f"processed_{timestamp}.wav")
    try:
        processor.process_file(input_file, output_file)
        return output_file, f"Processed with {len(processor.get_effects())} effects"
    except Exception as e:
        return None, f"Error processing file: {str(e)}"


def clear_all_effects():
    """Clear all effects in the chain"""
    processor.clear_effects()
    return "All effects cleared"


def remove_effect(effect_index):
    """Remove an effect by index"""
    if effect_index is None:
        return "No effect index provided"

    try:
        index = int(effect_index)
        removed = processor.remove_effect(index)
        if removed:
            return f"Removed {type(removed).__name__} from position {index}"
        else:
            return f"No effect found at position {index}"
    except ValueError:
        return "Invalid effect index"


# Create the Gradio interface
with gr.Blocks(title="Guitar Effects Processor") as app:
    gr.Markdown("# 🎸 Guitar Effects Processor")
    gr.Markdown("Process your guitar input with various effects in real-time or process audio files")

    with gr.Tab("Real-time Processing"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Controls")
                start_btn = gr.Button("Start Processing")
                stop_btn = gr.Button("Stop Processing")
                status_output = gr.Textbox(label="Status", value="Ready")

                start_btn.click(start_processing, inputs=[], outputs=[status_output])
                stop_btn.click(stop_processing, inputs=[], outputs=[status_output])

            with gr.Column(scale=2):
                gr.Markdown("## Effect Chain")
                effects_output = gr.Textbox(label="Current Effects Chain", value="No effects", lines=10)
                refresh_btn = gr.Button("Refresh Effects List")
                clear_btn = gr.Button("Clear All Effects")

                refresh_btn.click(get_current_effects, inputs=[], outputs=[effects_output])
                clear_btn.click(clear_all_effects, inputs=[], outputs=[effects_output])

        with gr.Row():
            with gr.Column():
                gr.Markdown("## Presets")
                preset_dropdown = gr.Dropdown(
                    ["None"] + list(presets.keys()),
                    label="Select Preset",
                    value="None"
                )
                apply_preset_btn = gr.Button("Apply Preset")
                preset_output = gr.Textbox(label="Preset Status")

                apply_preset_btn.click(
                    apply_preset,
                    inputs=[preset_dropdown],
                    outputs=[preset_output]
                ).then(
                    get_current_effects,
                    inputs=[],
                    outputs=[effects_output]
                )

            with gr.Column():
                gr.Markdown("## Add Individual Effect")
                effect_dropdown = gr.Dropdown(
                    ["None"] + list(individual_effects.keys()),
                    label="Select Effect",
                    value="None"
                )
                add_effect_btn = gr.Button("Add Effect")
                add_effect_output = gr.Textbox(label="Add Effect Status")

                add_effect_btn.click(
                    add_individual_effect,
                    inputs=[effect_dropdown],
                    outputs=[add_effect_output]
                ).then(
                    get_current_effects,
                    inputs=[],
                    outputs=[effects_output]
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown("## Modify Effect")
                effect_index = gr.Number(label="Effect Index", value=0, precision=0)
                param_name = gr.Textbox(label="Parameter Name (e.g., drive_db, mix, etc.)")
                param_value = gr.Number(label="Parameter Value")
                update_param_btn = gr.Button("Update Parameter")
                update_param_output = gr.Textbox(label="Update Status")

                update_param_btn.click(
                    update_effect_param,
                    inputs=[effect_index, param_name, param_value],
                    outputs=[update_param_output]
                ).then(
                    get_current_effects,
                    inputs=[],
                    outputs=[effects_output]
                )

            with gr.Column():
                gr.Markdown("## Remove Effect")
                remove_index = gr.Number(label="Effect Index to Remove", value=0, precision=0)
                remove_effect_btn = gr.Button("Remove Effect")
                remove_effect_output = gr.Textbox(label="Remove Status")

                remove_effect_btn.click(
                    remove_effect,
                    inputs=[remove_index],
                    outputs=[remove_effect_output]
                ).then(
                    get_current_effects,
                    inputs=[],
                    outputs=[effects_output]
                )

    with gr.Tab("File Processing"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Record Audio")
                record_seconds = gr.Slider(1, 30, value=5, step=1, label="Recording Duration (seconds)")
                record_btn = gr.Button("Record")
                record_output = gr.Textbox(label="Recording Status")
                recorded_audio = gr.Audio(label="Recorded Audio", type="filepath")

                record_btn.click(
                    record_audio,
                    inputs=[record_seconds],
                    outputs=[recorded_audio, record_output]
                )

        with gr.Row():
            with gr.Column():
                gr.Markdown("## Process Audio File")
                input_audio = gr.Audio(label="Input Audio", type="filepath")
                file_preset_dropdown = gr.Dropdown(
                    ["None"] + list(presets.keys()),
                    label="Apply Preset (Optional)",
                    value="None"
                )
                process_btn = gr.Button("Process Audio")
                process_output = gr.Textbox(label="Processing Status")
                processed_audio = gr.Audio(label="Processed Audio", type="filepath")

                process_btn.click(
                    process_audio_file,
                    inputs=[input_audio, file_preset_dropdown],
                    outputs=[processed_audio, process_output]
                )

    with gr.Tab("Help"):
        gr.Markdown("""
        # Guitar Effects Processor Help
        
        ## Real-time Processing
        1. Connect your guitar to your computer's audio input (using an audio interface).
        2. Click "Start Processing" to begin real-time effects processing.
        3. Apply a preset or add individual effects to the chain.
        4. Adjust effect parameters as needed.
        5. Click "Stop Processing" when you're done.
        
        ## File Processing
        1. Record audio directly or upload an audio file.
        2. Select an effects preset (optional).
        3. Click "Process Audio" to apply the current effects chain to the audio file.
        4. Download the processed audio file.
        
        ## Effect Parameters
        Common parameters for each effect:
        
        - **Compressor**: threshold_db, ratio, attack_ms, release_ms
        - **Distortion**: drive_db
        - **Chorus**: rate_hz, depth, mix
        - **Delay**: delay_seconds, feedback, mix
        - **Reverb**: room_size, damping, wet_level, dry_level
        - **Phaser**: rate_hz, depth, feedback, mix
        - **Gain**: gain_db
        - **LadderFilter**: cutoff_hz, resonance, drive
        - **Bitcrush**: bit_depth
        - **PitchShift**: semitones
        
        ## Tips
        - Start with a preset and then customize it by adding or removing effects
        - The order of effects matters! Try different arrangements for different sounds
        - For recording, ensure you have a clean input signal to avoid unwanted noise
        """)

# Launch the app
if __name__ == "__main__":
    app.launch()