"""
Audio Utils
"""

# Imports
import io
import os
import pretty_midi
import numpy as np
from scipy.io import wavfile

# Main Functions
def Utils_MIDI2WAV(midi_path, save_path):
    '''
    Utils - Convert MIDI to WAV format

    Reference: https://github.com/andfanilo/streamlit-midi-to-wav/blob/main/app.py
    '''
    # Read MIDI file
    midi_bytes = io.BytesIO(open(midi_path, "rb").read())
    # Convert MIDI data to WAV format
    midi_data = pretty_midi.PrettyMIDI(midi_bytes)
    audio_data = midi_data.fluidsynth()
    audio_data = np.int16(
        audio_data / np.max(np.abs(audio_data)) * 32767 * 0.9
    )  # -- Normalize for 16 bit audio https://github.com/jkanner/streamlit-audio/blob/main/helper.py
    virtual_file = io.BytesIO()
    wavfile.write(virtual_file, 44100, audio_data)
    virtual_file = virtual_file.read()
    # Write WAV file
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    open(save_path, "wb").write(virtual_file)