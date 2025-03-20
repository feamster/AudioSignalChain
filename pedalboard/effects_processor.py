# effects_processor.py
import numpy as np
import sounddevice as sd
import queue
import threading
import time
from pedalboard import Pedalboard, Plugin
from pedalboard.io import AudioFile
import os


class EffectsProcessor:
    def __init__(self, sample_rate=44100, block_size=512, channels=1):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.effects_chain = Pedalboard([])
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.is_running = False
        self.input_stream = None
        self.output_stream = None
        self.processing_thread = None

    def add_effect(self, effect):
        """Add an effect to the chain"""
        if isinstance(effect, Plugin):
            self.effects_chain.append(effect)
            return len(self.effects_chain) - 1  # Return the index of the added effect
        else:
            raise TypeError("Effect must be a pedalboard Plugin")

    def remove_effect(self, index):
        """Remove an effect from the chain by index"""
        if 0 <= index < len(self.effects_chain):
            removed = self.effects_chain.pop(index)
            return removed
        return None

    def clear_effects(self):
        """Remove all effects"""
        self.effects_chain.clear()

    def get_effects(self):
        """Get the current list of effects"""
        return self.effects_chain

    def update_effect_parameter(self, index, parameter_name, value):
        """Update a parameter of an effect by index"""
        if 0 <= index < len(self.effects_chain):
            if hasattr(self.effects_chain[index], parameter_name):
                setattr(self.effects_chain[index], parameter_name, value)
                return True
        return False

    def input_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f"Input status: {status}")
        # Put input data into the queue
        self.input_queue.put(indata.copy())

    def output_callback(self, outdata, frames, time, status):
        """Callback for audio output"""
        if status:
            print(f"Output status: {status}")

        try:
            # Get processed data from the queue
            outdata[:] = self.output_queue.get_nowait()
        except queue.Empty:
            # If no data is available, output silence
            outdata.fill(0)

    def process_audio(self):
        """Process audio from input to output queue"""
        while self.is_running:
            try:
                # Get input data
                indata = self.input_queue.get(timeout=1.0)

                # Process the audio through the effects chain
                if len(self.effects_chain) > 0:
                    processed = self.effects_chain(indata, self.sample_rate)
                else:
                    processed = indata

                # Put processed data into the output queue
                self.output_queue.put(processed)
            except queue.Empty:
                continue

    def start(self):
        """Start audio processing"""
        if self.is_running:
            return

        self.is_running = True

        # Start the processing thread
        self.processing_thread = threading.Thread(target=self.process_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()

        # Start audio input stream
        self.input_stream = sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            callback=self.input_callback
        )

        # Start audio output stream
        self.output_stream = sd.OutputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            callback=self.output_callback
        )

        self.input_stream.start()
        self.output_stream.start()

        print("Audio processing started")

    def stop(self):
        """Stop audio processing"""
        if not self.is_running:
            return

        self.is_running = False

        # Wait for processing thread to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)

        # Stop audio streams
        if self.input_stream:
            self.input_stream.stop()
            self.input_stream.close()
            self.input_stream = None

        if self.output_stream:
            self.output_stream.stop()
            self.output_stream.close()
            self.output_stream = None

        # Clear queues
        while not self.input_queue.empty():
            self.input_queue.get_nowait()

        while not self.output_queue.empty():
            self.output_queue.get_nowait()

        print("Audio processing stopped")

    def process_file(self, input_file, output_file):
        """Process an audio file through the current effects chain"""
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

        # Read input audio file
        with AudioFile(input_file) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate

        # Process audio through effects chain
        processed = self.effects_chain(audio, samplerate)

        # Write processed audio to output file
        with AudioFile(output_file, 'w', samplerate, processed.shape[0]) as f:
            f.write(processed)

        return output_file