import os
import sounddevice as sd
import numpy as np
import wave
from typing import Tuple  # Added this import

from pedalboard_native import Compressor, Bitcrush
from pydub import AudioSegment
from pydub.effects import normalize, speedup
from pedalboard import Pedalboard, Reverb, Delay, Chorus, Phaser
import librosa
import scipy.signal as signal

# Constants
AUDIO_DIR = "audio"
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH = 2

# Import the metronome functions from the new file
from metronome import record_with_metronome


def add_effects(audio_data, sample_rate):
    # Get the raw audio data as numpy array
    samples = np.array(audio_data.get_array_of_samples())

    # Preserve the original data type and range
    if audio_data.sample_width == 2:  # 16-bit audio
        samples = samples.astype(np.float32) / 32768.0
    else:  # Assume 32-bit audio
        samples = samples.astype(np.float32) / 2147483648.0

    # Handle stereo to mono conversion if needed
    if audio_data.channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)

    # Create and apply effects
    board = Pedalboard([
        Reverb(room_size=0.3, wet_level=0.2),
        Delay(delay_seconds=0.25),
        Chorus(rate_hz=0.5, depth=0.5, centre_delay_ms=7.0, feedback=0.5, mix=0.5),
        Compressor(),
        Phaser(rate_hz=0.5, depth=0.5, centre_frequency_hz=1300.0, feedback=0.5, mix=0.5),
        # Bitcrush(bit_depth=8)
    ])

    # Process audio through effects
    effected = board.process(samples, sample_rate)

    # Convert back to the original range
    if audio_data.sample_width == 2:
        effected = (effected * 32768.0).astype(np.int16)
    else:
        effected = (effected * 2147483648.0).astype(np.int32)

    return effected, sample_rate


def add_effects_from_file(audio_path):
    # Load audio file using AudioSegment to preserve metadata
    audio_data = AudioSegment.from_file(audio_path)
    return add_effects(audio_data, audio_data.frame_rate)


def create_loop(audio_data, num_loops=1):
    samples = np.array(audio_data.get_array_of_samples())

    if audio_data.sample_width == 2:
        samples = samples.astype(np.float32) / 32768.0
    else:
        samples = samples.astype(np.float32) / 2147483648.0

    if audio_data.channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)

    looped = np.tile(samples, num_loops)

    if audio_data.sample_width == 2:
        looped = (looped * 32768.0).astype(np.int16)
    else:
        looped = (looped * 2147483648.0).astype(np.int32)

    # Convert the numpy array back to AudioSegment
    return AudioSegment(
        data=looped.tobytes(),
        sample_width=audio_data.sample_width,
        frame_rate=audio_data.frame_rate,
        channels=1
    )


def create_loop_from_file(audio_path, num_loops=4):
    audio_data = AudioSegment.from_file(audio_path)
    return create_loop(audio_data, num_loops)


def apply_highpass_filter(audio, cutoff_freq, sample_rate):
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_freq / nyquist
    b, a = signal.butter(1, normal_cutoff, btype='high', analog=False)
    filtered_audio = signal.lfilter(b, a, np.array(audio.get_array_of_samples()))
    return AudioSegment(data=filtered_audio.tobytes(), sample_width=audio.sample_width, frame_rate=audio.frame_rate,
                        channels=audio.channels)


def record_audio(output_file: object, record_seconds: object = 5, sample_rate: object = 44100,
                 channels: object = 1) -> None:
    # Find the Scarlett Focusrite device index
    device_index = None
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']}")
        if 'Aggregate' in device['name']:
            device_index = i
            channels = 2
            break
    if device_index is None:
        raise ValueError("Scarlett Focusrite device not found")

    print(f"Recording for {record_seconds} seconds...")  # f-string (recommended)
    audio_data = sd.rec(int(record_seconds * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16',
                        device=device_index)
    sd.wait()
    print("Finished recording.")

    with wave.open(output_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())


def calculate_record_seconds(num_bars, tempo_bpm, playback_speed, num_loops):
    """
    Calculate required recording duration to achieve desired bars after processing.

    Args:
        num_bars (int): Number of bars desired in final output
        tempo_bpm (float): Tempo in beats per minute
        playback_speed (float): Speed multiplier (e.g., 1.25 for 25% faster)
        num_loops (int): Number of times the audio will be looped

    Returns:
        float: Required recording duration in seconds
    """
    seconds_per_beat = 60.0 / tempo_bpm
    seconds_per_bar = seconds_per_beat * 4  # Assuming 4/4 time signature
    final_duration = num_bars * seconds_per_bar

    # Work backwards through the processing chain
    duration_before_loops = final_duration / num_loops
    record_duration = duration_before_loops * playback_speed

    return record_duration


def ensure_directory_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def setup_audio_paths() -> Tuple[str, str]:
    """Set up the input and output audio file paths."""
    ensure_directory_exists(AUDIO_DIR)
    input_path = os.path.join(AUDIO_DIR, "input.wav")
    output_path = os.path.join(AUDIO_DIR, "output.wav")
    return input_path, output_path


def process_audio(
        input_file: str,
        output_file: str,
        playback_speed: float,
        num_loops: int,
        cutoff_freq: float = 1000.0
) -> None:
    """Process audio with a chain of effects."""
    # Load the recorded audio
    audio = AudioSegment.from_wav(input_file)
    sample_rate = audio.frame_rate

    # Apply processing chain
    audio = normalize(audio)

    # Add effects and convert back to AudioSegment
    audio_with_effects, sr = add_effects(audio, sample_rate=sample_rate)
    audio = AudioSegment(
        audio_with_effects.tobytes(),
        frame_rate=sr,
        sample_width=DEFAULT_SAMPLE_WIDTH,
        channels=DEFAULT_CHANNELS
    )

    # Apply speed and direction changes

    if (playback_speed > 1):
        audio = speedup(audio, playback_speed)

    # Reverse the audio
    audio = audio.reverse()

    # Apply filter and create loop
    #audio = apply_highpass_filter(audio, cutoff_freq, sample_rate)
    audio = create_loop(audio, num_loops)

    # Export the processed audio
    audio.export(output_file, format="wav")
    print(f"Processed audio saved to {output_file}")


def play_audio_file(file_path: str) -> None:
    """Play an audio file and wait for it to finish."""
    print(f"Playing audio from {file_path}...")
    audio_data, sample_rate = librosa.load(file_path)
    sd.play(audio_data, sample_rate)
    sd.wait()


def main():
    # Configuration parameters
    num_bars = 4
    target_tempo = 120
    playback_speed = 1.0
    num_loops = 1
    cutoff_freq = 1000.0

    # Calculate recording duration
    record_seconds = calculate_record_seconds(
        num_bars=num_bars,
        tempo_bpm=target_tempo,
        playback_speed=playback_speed,
        num_loops=num_loops
    )

    # Setup input and output paths
    input_file, output_file = setup_audio_paths()

    # Record audio
    record_audio(input_file, record_seconds)

    # Process and play the audio
    process_audio(input_file, output_file, playback_speed, num_loops, cutoff_freq)
    play_audio_file(output_file)


if __name__ == "__main__":
    main()
