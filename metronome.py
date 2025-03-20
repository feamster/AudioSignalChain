import time
import threading
import soundfile as sf
import sounddevice as sd


def metronome_click(bpm, recording_duration):
    """
    Play metronome clicks at a given BPM for the duration of the recording.

    :param bpm: Beats per minute (integer).
    :param recording_duration: Total duration to keep the metronome active, in seconds.
    """
    # Calculate interval between each beat (seconds)
    beat_interval = 60.0 / bpm

    # Keep playing the click sound for the duration of the recording
    end_time = time.time() + recording_duration
    while time.time() < end_time:
        try:
            # Read the .wav file
            data, sample_rate = sf.read("metronome_click.wav", dtype='float32')
            # Play the audio
            sd.play(data, samplerate=sample_rate)
            time.sleep(beat_interval)  # Wait for the next beat
            sd.wait()  # Wait for playback to finish
        except Exception as e:
            print(f"Error: {e}")


def record_with_metronome(audio_file, bpm, record_seconds, record_audio_func):
    """
    Record audio while playing a metronome click.

    :param audio_file: Path to save the recorded audio.
    :param bpm: Target tempo in beats per minute.
    :param record_seconds: Duration of the recording in seconds.
    :param record_audio_func: Function to record audio
    """
    # Start metronome in a separate thread
    metronome_thread = threading.Thread(target=metronome_click, args=(bpm, record_seconds))
    metronome_thread.start()

    # Start audio recording using the provided function
    record_audio_func(audio_file, record_seconds)

    # Wait for the metronome to finish
    metronome_thread.join()