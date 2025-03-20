# effect_presets.py
from pedalboard import (
    Chorus, Delay, Distortion, Gain, Reverb,
    Phaser, Compressor, Limiter, LadderFilter,
    Bitcrush, PitchShift, Pedalboard
)


def create_clean_preset():
    """Create a clean guitar preset"""
    return Pedalboard([
        Compressor(threshold_db=-20, ratio=3),
        Gain(gain_db=3),
        Reverb(room_size=0.2, dry_level=0.8, wet_level=0.2)
    ])


def create_blues_preset():
    """Create a blues guitar preset"""
    return Pedalboard([
        Compressor(threshold_db=-20, ratio=4),
        Distortion(drive_db=10),
        Gain(gain_db=5),
        Reverb(room_size=0.3, dry_level=0.7, wet_level=0.3)
    ])


def create_rock_preset():
    """Create a rock guitar preset"""
    return Pedalboard([
        Compressor(threshold_db=-24, ratio=4),
        Distortion(drive_db=20),
        Gain(gain_db=8),
        Reverb(room_size=0.2, dry_level=0.8, wet_level=0.2)
    ])


def create_metal_preset():
    """Create a metal guitar preset"""
    return Pedalboard([
        Compressor(threshold_db=-30, ratio=6),
        Distortion(drive_db=30),
        Gain(gain_db=10),
        LadderFilter(cutoff_hz=2000, resonance=0.7, drive=1.5),
        Reverb(room_size=0.1, dry_level=0.9, wet_level=0.1)
    ])


def create_ambient_preset():
    """Create an ambient guitar preset"""
    return Pedalboard([
        Compressor(threshold_db=-20, ratio=3),
        Gain(gain_db=3),
        Chorus(rate_hz=0.7, depth=0.6, feedback=0.4, mix=0.5),
        Delay(delay_seconds=0.5, feedback=0.4, mix=0.4),
        Reverb(room_size=0.8, dry_level=0.3, wet_level=0.7)
    ])


def create_psychedelic_preset():
    """Create a psychedelic guitar preset"""
    return Pedalboard([
        Phaser(rate_hz=0.8, depth=0.8, feedback=0.5, mix=0.6),
        Delay(delay_seconds=0.3, feedback=0.6, mix=0.5),
        Chorus(rate_hz=1.0, depth=0.7, feedback=0.5, mix=0.6),
        Reverb(room_size=0.7, dry_level=0.4, wet_level=0.6)
    ])


def create_lofi_preset():
    """Create a lo-fi guitar preset"""
    return Pedalboard([
        Bitcrush(bit_depth=8),
        LadderFilter(cutoff_hz=3000, resonance=0.5, mode=LadderFilter.Mode.HPF12),
        Delay(delay_seconds=0.1, feedback=0.3, mix=0.3),
        Reverb(room_size=0.6, dry_level=0.5, wet_level=0.5)
    ])


def get_effect_presets():
    """Get all available effect presets"""
    return {
        "Clean": create_clean_preset,
        "Blues": create_blues_preset,
        "Rock": create_rock_preset,
        "Metal": create_metal_preset,
        "Ambient": create_ambient_preset,
        "Psychedelic": create_psychedelic_preset,
        "Lo-Fi": create_lofi_preset,
    }


def get_individual_effects():
    """Get individual effects that can be added"""
    return {
        "Compressor": lambda: Compressor(threshold_db=-20, ratio=3),
        "Distortion": lambda: Distortion(drive_db=15),
        "Chorus": lambda: Chorus(rate_hz=0.7, depth=0.6),
        "Delay": lambda: Delay(delay_seconds=0.4, feedback=0.4),
        "Reverb": lambda: Reverb(room_size=0.5),
        "Phaser": lambda: Phaser(rate_hz=0.8, depth=0.6),
        "Gain": lambda: Gain(gain_db=5),
        "Filter": lambda: LadderFilter(cutoff_hz=2000, resonance=0.5),
        "Bitcrush": lambda: Bitcrush(bit_depth=8),
        "PitchShift": lambda: PitchShift(semitones=0)
    }