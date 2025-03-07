import sounddevice as sd
import numpy as np
import time
from threading import Thread
import queue


class AudioCapture:
    def __init__(self, sample_rate=44100, channels=1, chunk_size=1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.recording = False
        self.audio_queue = queue.Queue()
        self.recorded_data = []

    def audio_callback(self, indata, frames, time_info, status):
        """Callback function for the audio stream"""
        if status:
            print(f"Status: {status}")
        self.audio_queue.put(indata.copy())
        if self.recording:
            self.recorded_data.append(indata.copy())

    def list_devices(self):
        """List all available audio devices"""
        print("\nAvailable Audio Devices:")
        print("-" * 50)
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            print(f"{i}: {dev['name']} (Inputs: {dev['max_input_channels']}, "
                  f"Outputs: {dev['max_output_channels']})")
        print("-" * 50)

    def start_recording(self, device=None):
        """Start recording audio"""
        try:
            self.recording = True
            self.recorded_data = []
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self.audio_callback,
                blocksize=self.chunk_size,
                device=device
            )
            self.stream.start()
            print("Recording started...")
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.recording = False

    def stop_recording(self):
        """Stop recording and return the recorded audio"""
        if not self.recording:
            return None

        self.recording = False
        self.stream.stop()
        self.stream.close()

        if self.recorded_data:
            # Concatenate all recorded chunks
            recorded_array = np.concatenate(self.recorded_data, axis=0)
            return recorded_array
        return None

    def save_recording(self, filename, data):
        """Save the recording to a file"""
        try:
            import soundfile as sf
            sf.write(filename, data, self.sample_rate)
            print(f"Recording saved to {filename}")
        except Exception as e:
            print(f"Error saving recording: {e}")


def main():
    # Create an instance of AudioCapture
    audio = AudioCapture()

    # Show available devices
    audio.list_devices()

    # Let user select device
    device_id = input("\nEnter device ID to use (press Enter for default): ").strip()
    device = None if not device_id else int(device_id)

    print("\nCommands:")
    print("'r' - start recording")
    print("'s' - stop recording")
    print("'q' - quit")

    while True:
        command = input("\nEnter command: ").lower()

        if command == 'r':
            audio.start_recording(device)
        elif command == 's':
            recorded_data = audio.stop_recording()
            if recorded_data is not None:
                filename = f"recording_{int(time.time())}.wav"
                audio.save_recording(filename, recorded_data)
        elif command == 'q':
            if audio.recording:
                audio.stop_recording()
            break
        else:
            print("Invalid command")


if __name__ == "__main__":
    main()