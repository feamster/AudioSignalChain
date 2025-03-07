#%% md
# # Chord Player Interface
# 
# This Jupyter notebook implements a simple web interface using Gradio that allows users to select and play musical chords. The interface provides options to choose the chord type (Major or Minor) and the root note, then plays the selected chord using the SimpleChordPlayer class.
#%%
import gradio as gr
#%%
import gradio as gr
import numpy as np
import sounddevice as sd

# Define note frequencies (A4 = 440Hz as reference)
NOTE_FREQUENCIES = {
    'C4': 261.63,
    'D4': 293.66,
    'E4': 329.63,
    'F4': 349.23,
    'G4': 392.00,
    'A4': 440.00,
    'B4': 493.88
}


def generate_sine_wave(frequency, duration, sample_rate=44100):
    """Generate a sine wave for the given frequency and duration."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * frequency * t)


def play_chord(root_note, chord_type):
    """Play a chord based on root note and chord type."""
    # Define chord intervals (semitones from root)
    intervals = [0, 4, 7] if chord_type == "Major" else [0, 3, 7]

    # Get root frequency
    root_freq = NOTE_FREQUENCIES[root_note]

    # Calculate chord frequencies
    frequencies = [root_freq * (2 ** (interval / 12)) for interval in intervals]

    # Generate and mix sine waves
    duration = 1.0
    sample_rate = 44100
    mixed_signal = np.zeros(int(sample_rate * duration))

    for freq in frequencies:
        mixed_signal += generate_sine_wave(freq, duration, sample_rate)

    # Normalize and play
    mixed_signal = mixed_signal / len(frequencies)
    sd.play(mixed_signal, sample_rate)
    sd.wait()

    return f"Playing {root_note} {chord_type} chord"


# Create Gradio interface
interface = gr.Interface(
    fn=play_chord,
    inputs=[
        gr.Dropdown(choices=list(NOTE_FREQUENCIES.keys()), label="Root Note"),
        gr.Dropdown(choices=["Major", "Minor"], label="Chord Type")
    ],
    outputs=gr.Text(label="Status"),
    title="Simple Chord Player",
    description="Select a root note and chord type, then click submit to play the chord."
)

if __name__ == "__main__":
    interface.launch()
#%%
def play_chord(root_note, chord_type):
    # Create chord player instance
    chord_player = SimpleChordPlayer()

    # Define chord intervals
    if chord_type == "Major":
        intervals = [0, 4, 7]  # Major chord intervals
    else:
        intervals = [0, 3, 7]  # Minor chord intervals

    # Get root frequency
    root_freq = NOTE_FREQUENCIES[root_note]

    # Calculate chord frequencies
    chord_freqs = [root_freq * (2 ** (interval/12)) for interval in intervals]

    # Play the chord
    chord_player.play_chord(chord_freqs, duration=1.0)

    return f"Playing {root_note} {chord_type} chord"

# Define available options
notes = list(NOTE_FREQUENCIES.keys())
chord_types = ["Major", "Minor"]
#%%
# Create Gradio interface
interface = gr.Interface(
    fn=play_chord,
    inputs=[
        gr.Dropdown(choices=notes, label="Root Note"),
        gr.Dropdown(choices=chord_types, label="Chord Type")
    ],
    outputs=gr.Text(label="Status"),
    title="Simple Chord Player",
    description="Select a root note and chord type, then click submit to play the chord."
)

# Launch the interface
interface.launch()