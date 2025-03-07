import gradio as gr
import numpy as np
import sounddevice as sd
import queue
import threading
from typing import List, Tuple, Optional

# Define note frequencies (A4 = 440Hz as reference)
NOTE_FREQUENCIES = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88
}


class AudioRecorder:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_queue = queue.Queue()
        self.recorded_audio = None
        self.loop_thread = None
        self.looping = False

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        if self.recording:
            self.audio_queue.put(indata.copy())

    def start_recording(self, device: Optional[int] = None) -> None:
        self.recording = True
        self.audio_queue = queue.Queue()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.callback,
            device=device
        )
        self.stream.start()

    def stop_recording(self) -> np.ndarray:
        self.recording = False
        self.stream.stop()
        self.stream.close()

        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())

        if audio_chunks:
            self.recorded_audio = np.concatenate(audio_chunks)
            return self.recorded_audio
        return np.array([])

    def play_loop(self):
        while self.looping and self.recorded_audio is not None:
            sd.play(self.recorded_audio, self.sample_rate)
            sd.wait()

    def start_loop(self):
        if self.recorded_audio is not None:
            self.looping = True
            self.loop_thread = threading.Thread(target=self.play_loop)
            self.loop_thread.start()

    def stop_loop(self):
        self.looping = False
        if self.loop_thread:
            self.loop_thread.join()


def generate_sine_wave(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * frequency * t)


def get_available_devices():
    devices = sd.query_devices()
    input_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(f"{i}: {device['name']}")
    return input_devices


recorder = AudioRecorder()


def play_chord(root_note: str, chord_type: str) -> str:
    intervals = [0, 4, 7] if chord_type == "Major" else [0, 3, 7]
    root_freq = NOTE_FREQUENCIES[root_note]
    frequencies = [root_freq * (2 ** (interval / 12)) for interval in intervals]

    duration = 1.0
    sample_rate = 44100
    mixed_signal = np.zeros(int(sample_rate * duration))

    for freq in frequencies:
        mixed_signal += generate_sine_wave(freq, duration, sample_rate)

    mixed_signal = mixed_signal / len(frequencies)
    sd.play(mixed_signal, sample_rate)
    sd.wait()

    return f"Playing {root_note} {chord_type} chord"


def start_recording(device_str: str) -> str:
    device_idx = int(device_str.split(':')[0])
    recorder.start_recording(device_idx)
    return "Recording started..."


def stop_recording() -> Tuple[str, np.ndarray]:
    audio = recorder.stop_recording()
    return "Recording stopped", audio


def toggle_loop(audio: np.ndarray, state: bool) -> str:
    if state:
        recorder.recorded_audio = audio
        recorder.start_loop()
        return "Loop playing..."
    else:
        recorder.stop_loop()
        return "Loop stopped"


# Create Gradio interface with tabs
with gr.Blocks() as interface:
    gr.Markdown("# Audio Playground")

    with gr.Tab("Chord Player"):
        with gr.Row():
            root_note = gr.Dropdown(
                choices=list(NOTE_FREQUENCIES.keys()),
                label="Root Note"
            )
            chord_type = gr.Dropdown(
                choices=["Major", "Minor"],
                label="Chord Type"
            )
        chord_output = gr.Text(label="Status")
        play_btn = gr.Button("Play Chord")
        play_btn.click(
            play_chord,
            inputs=[root_note, chord_type],
            outputs=[chord_output]
        )

    with gr.Tab("Audio Recorder"):
        with gr.Row():
            device_dropdown = gr.Dropdown(
                choices=get_available_devices(),
                label="Input Device"
            )
        with gr.Row():
            record_btn = gr.Button("Start Recording")
            stop_btn = gr.Button("Stop Recording")

        status_text = gr.Text(label="Recording Status")
        audio_output = gr.Audio(label="Recorded Audio")

        loop_toggle = gr.Checkbox(label="Loop Playback")
        loop_status = gr.Text(label="Loop Status")

        record_btn.click(
            start_recording,
            inputs=[device_dropdown],
            outputs=[status_text]
        )

        stop_btn.click(
            stop_recording,
            outputs=[status_text, audio_output]
        )

        loop_toggle.change(
            toggle_loop,
            inputs=[audio_output, loop_toggle],
            outputs=[loop_status]
        )

if __name__ == "__main__":
    interface.launch()