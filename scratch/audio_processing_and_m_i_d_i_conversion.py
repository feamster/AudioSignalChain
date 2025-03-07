import sounddevice as sd
import numpy as np
import wave
from pydub import AudioSegment
import librosa
import midiutil
from pedalboard import Pedalboard, Reverb, Delay, Chorus
#from basic_pitch.inference import predict_and_save


def add_effects(audio_path):
    # Load audio file
    y, sr = librosa.load(audio_path)

    # Create a pedalboard with effects
    board = Pedalboard([
        Reverb(room_size=0.8),
        Delay(delay_seconds=0.25),
        Chorus()
    ])

    # Process the audio
    effected = board.process(y, sr)

    return effected, sr


def create_loop(audio_path, num_loops=4):
    # Load audio
    y, sr = librosa.load(audio_path)

    # Find beats
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

    # Get beat frames
    beat_frames = librosa.frames_to_samples(beats)

    # Create loop (for example, first 4 beats)
    if len(beat_frames) >= 4:
        loop_end = beat_frames[4]
        loop_segment = y[:loop_end]

        # Create the loop
        looped = np.tile(loop_segment, num_loops)
        return looped, sr
    return y, sr


def audio_to_midi(audio_path, output_midi_path):
    """Convert audio to MIDI using basic-pitch"""
    # This will create a MIDI file
    predict_and_save(
        audio_path_list=[audio_path],
        output_directory="./",
        save_midi=True,
        midi_path=output_midi_path
    )


def main():
    input_file = "../input.wav"
    output_file = "../output.wav"
    midi_file = "output.mid"

    # Record audio (using your existing record_audio function)
    record_seconds = 5
    record_audio(input_file, record_seconds)

    # Add effects
    audio_with_effects, sr = add_effects(input_file)

    # Create a loop
    looped_audio, sr = create_loop(input_file)

    # Save processed audio
    import soundfile as sf
    sf.write(output_file, looped_audio, sr)

    # Convert to MIDI
    audio_to_midi(input_file, midi_file)

    print(f"Processed audio saved to {output_file}")
    print(f"MIDI file saved to {midi_file}")


if __name__ == "__main__":
    main()