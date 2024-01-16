"""
Piano Music Generator Library

References:
 - https://medium.com/@stevehiehn/how-to-generate-music-with-python-the-basics-62e8ea9b99a5
"""

# Imports
from mingus.core import chords
from midiutil import MIDIFile

# Main Vars
AVAILABLE_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
NOTES_ACCIDENTALS_MAP = {
    "Db": "C#",
    "D#": "Eb",
    "E#": "F",
    "Gb": "F#",
    "G#": "Ab",
    "A#": "Bb",
    "B#": "C"
}
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(AVAILABLE_NOTES)

# Main Functions
## Chord Functions
def Chord_GeteNotes_FromShorthand(chord_shorthand):
    '''
    Chord - Get Notes for the given chord written in shorthand notation
    '''
    return chords.from_shorthand(chord_shorthand)

## Note Functions
def Note_SwapAccidentals(note):
    '''
    Note - Swap accidental notes, i.e. replace all 'Db' with 'C#' and so on for all same notes
    '''
    if note in NOTES_ACCIDENTALS_MAP.keys(): return NOTES_ACCIDENTALS_MAP[note]
    return note

def Note_ToNumber(note, octave=4):
    '''
    Note - Convert note to number
    '''
    try:
        note = Note_SwapAccidentals(note)
        note = AVAILABLE_NOTES.index(note)
        note += (NOTES_IN_OCTAVE * octave)
    except ValueError:
        note = -1

    return note

def Note_ResolveNotesWithCommonParams(notes, common_params={}):
    '''
    Note - Resolve notes data with common parameters
    '''
    # Init
    notes_resolved = []
    # Resolve
    for i in range(len(notes)):
        note_resolved = dict(notes[i])
        for cpk in common_params.keys():
            if cpk not in notes[i].keys():
                note_resolved[cpk] = common_params[cpk]
        notes_resolved.append(note_resolved)
    
    return notes_resolved

# MIDI Functions
def MIDI_AddTrack(notes, MIDIAudio=None, track=0, start_time=0, tempo=120):
    '''
    MIDI - Add a new track to the MIDI audio
    Parameters:
     - MIDIAudio : MIDI audio, if not provided a new one will be created
     - track : MIDI track number to add the notes to (taken as 0 if missing)
     - start_time : Start time for the new track (In beats) (taken as 0 beats if missing)
     - tempo : MIDI tempo (In beats per minute) (taken as 120 beats per minute if missing)

    Each note should have the keys,
     - "channel" : MIDI channel (taken as 0 if missing)
     - "pitch" (0 - 127) : MIDI pitch value
     - "key" (MUST be a note) : MIDI key (ignored if pitch is given)
     - "octave" (0 - 7) : MIDI octave value (ignored if pitch is given and taken as 4 if missing)
     - "delay" : Delay between the current note and previous note (Must be include duration of previous note to avoid overlapping)
     - "duration" : MIDI note duration (taken as 1 beat if missing)
     - "volume" (0 - 127) : MIDI volume value (taken as 100 if missing)
    '''
    # Init
    # Create MIDI if not present
    if not MIDIAudio: MIDIAudio = MIDIFile(1) # One track, defaults to format 1 (tempo track is created automatically)
    # Add track
    MIDIAudio.addTempo(track, start_time, tempo)
    # Add notes
    cur_time = start_time
    for i, note in enumerate(notes):
        ## Update current time (done regardless of whether note is valid or not)
        cur_time += note["delay"]
        ## Check for missing / invalid note parameters
        if "octave" not in note.keys(): note["octave"] = 4
        if "pitch" not in note.keys() and "key" in note.keys():
            note["pitch"] = Note_ToNumber(note["key"], note["octave"])
        if note["pitch"] < 0 and note["pitch"] > 127: continue
        if "channel" not in note.keys(): note["channel"] = 0
        if "duration" not in note.keys(): note["duration"] = 1
        if "volume" not in note.keys(): note["volume"] = 100
        ## Add note if valid pitch
        MIDIAudio.addNote(track, note["channel"], note["pitch"], cur_time, note["duration"], note["volume"])

    return MIDIAudio

## Audio Generator Functions
def AudioGen_SaveMIDI(MIDIAudio, save_path="Data/GeneratedAudio/generated_midi.mid"):
    '''
    Audio Generator - Save MIDI file
    '''
    with open(save_path, "wb") as output_file:
        MIDIAudio.writeFile(output_file)

# RunCode
# ## Params
# OCTAVE = 4
# chord_progression = ["Cmaj7", "Fmaj7"]
# ## Convert to Note Numbers
# note_letters = []
# for chord in chord_progression:
#     note_letters.extend(chords.from_shorthand(chord))
# note_numbers = []
# for note in note_letters:
#     note_numbers.append(Note_ToNumber(note, OCTAVE))
# ## Make MIDI
# AudioGen_CreateMIDI(note_numbers)