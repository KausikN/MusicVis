"""
Music Generator Library - Piano

References:
- https://medium.com/@stevehiehn/how-to-generate-music-with-python-the-basics-62e8ea9b99a5
"""

# Imports
import os
from midiutil import MIDIFile
from mido import MidiFile as MidiFile_Read, Message, MetaMessage
from mingus.core import chords as LIBRARY_CHORDS, notes as LIBRARY_NOTES, keys as LIBRARY_KEYS

# Main Vars
AVAILABLE_NOTES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
NOTES_ACCIDENTALS_MAP = {
    # General Accidentals
    "Db": "C#",
    "D#": "Eb",
    "E#": "F",
    "Fb": "E",
    "Gb": "F#",
    "G#": "Ab",
    "A#": "Bb",
    "B#": "C",
    "Cb": "B"
}
NOTES_IN_OCTAVE = len(AVAILABLE_NOTES)
OCTAVES = list(range(NOTES_IN_OCTAVE-1))
NOTE_VALUE_RANGE = [0, 127]
CHORDS = {}
TRACKS = {}

# Main Functions
## Chord Functions
def Chord_GetNotes_FromShorthand(chord_shorthand):
    '''
    Chord - Get Notes for the given chord written in shorthand notation
    '''
    return LIBRARY_CHORDS.from_shorthand(chord_shorthand)

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
        note = AVAILABLE_NOTES.index(note)
        note += (NOTES_IN_OCTAVE * octave)
    except ValueError:
        note = -1

    return note

def Note_FromNumber(number):
    '''
    Note - Convert number to note
    '''
    note = {
        "note": AVAILABLE_NOTES[number % NOTES_IN_OCTAVE],
        "octave": int(number // NOTES_IN_OCTAVE)
    }

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

def Note_DecomposeNotesToKeys(notes, common_params={}):
    '''
    Note - Decompose notes with tracks, chords and keys to keys
    '''
    # Init
    KEYS = []
    # Reformat notes if needed
    for i in range(len(notes)):
        if type(notes[i]) == str: notes[i] = {"note": notes[i]}
    # Decompose notes
    for i in range(len(notes)):
        keys_decomposed_current = []
        note = notes[i]
        ## Check if track
        if note["note"] in TRACKS.keys():
            ### Recursively decompose the track
            keys_decomposed_current = Note_DecomposeNotesToKeys(TRACKS[note["note"]]["notes"], TRACKS[note["note"]]["common_params"])
        ## Check if chord or key
        else:
            ### Check if chord
            keys_stack = []
            chord_check = False
            chord_marker = "_"
            if note["note"].startswith(chord_marker):
                note["note"] = note["note"][len(chord_marker):]
                try:
                    ### Get Notes for the Chord
                    ChordNotes = Chord_GetNotes_FromShorthand(note["note"])
                    for cni in range(len(ChordNotes)):
                        cnd = dict(note)
                        cnd["note"] = ChordNotes[cni] # Set the current note in the chord
                        if cni > 0: cnd["delay"] = 0 # Only the first note in a chord will have the delay
                        keys_stack.append(cnd)
                    chord_check = True
                except Exception as e:
                    # print(e)
                    pass
            ### If nothing, it is a key
            if not chord_check:
                keys_stack = [note]
            ### Add Keys Stack
            for cur_note in keys_stack:
                #### All keys should have first letter in upper case and all other letters in lower case
                if len(cur_note["note"]) > 1:
                    cur_note["note"] = cur_note["note"][:1].upper() + cur_note["note"][1:].lower()
                #### Clean redundant, extra and wrong accidentals
                cur_note["note"] = LIBRARY_NOTES.remove_redundant_accidentals(cur_note["note"])
                cur_note["note"] = LIBRARY_NOTES.reduce_accidentals(cur_note["note"])
                cur_note["note"] = Note_SwapAccidentals(cur_note["note"])
                #### Append
                keys_decomposed_current.append(cur_note)
        
        KEYS.extend(keys_decomposed_current)

    # Resolve Notes with Common Params
    KEYS = Note_ResolveNotesWithCommonParams(KEYS, common_params)
    # Add note number as value parameter for all notes
    for i in range(len(KEYS)):
        KEYS[i]["value"] = Note_ToNumber(KEYS[i]["note"], KEYS[i]["octave"])

    return KEYS

# MIDI Functions
def MIDI_AddTrack(notes, MIDIAudio=None, track=0, start_time=0, tempo=60):
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
     - "note" (MUST be a note) : MIDI key (ignored if pitch is given)
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
        else: note["octave"] = int(note["octave"])
        if "pitch" not in note.keys():
            if "value" in note.keys(): note["pitch"] = note["value"]
            elif "note" in note.keys(): note["pitch"] = Note_ToNumber(note["note"], note["octave"])
            else: note["pitch"] = -1
        if note["pitch"] < 0 and note["pitch"] > 127: continue
        if "channel" not in note.keys(): note["channel"] = 0
        else: note["channel"] = int(note["channel"])
        if "duration" not in note.keys(): note["duration"] = 1
        else: note["duration"] = float(note["duration"])
        if "volume" not in note.keys(): note["volume"] = 100
        else: note["volume"] = int(note["volume"])
        ## Add note if valid pitch (If not valid, make pitch as 0)
        if note["pitch"] < 0 or note["pitch"] > 255: note["pitch"] = 0
        MIDIAudio.addNote(track, note["channel"], note["pitch"], cur_time, note["duration"], note["volume"])

    return MIDIAudio

def MIDI_ExtractNotes(MIDIAudio, clip_time=(-1, -1), speed=1.0):
    '''
    MIDI - Extract Notes from MIDI Audio Object
    '''
    # Init
    TRACKS = MIDIAudio.tracks
    NOTES = []
    # For each track, extract notes
    for track in TRACKS:
        MESSAGES = [message for message in track if isinstance(message, Message)]
        if len(MESSAGES) == 0: continue
        track_notes = []
        cur_time = 0
        cur_delay = 0
        for message in MESSAGES:
            cur_time += message.time/1000
            if clip_time[0] > -1 and cur_time < clip_time[0]:
                cur_delay = -(clip_time[0]-cur_time)
                continue
            if clip_time[1] > -1 and cur_time > clip_time[1]:
                cur_time = clip_time[1]
                break
            cur_delay += message.time/1000
            if message.type == "note_on" and message.velocity > 0:
                cur_note = Note_FromNumber(message.note)
                track_notes.append({
                    "note": cur_note["note"],
                    "delay": cur_delay,
                    "duration": None,
                    "octave": cur_note["octave"],
                    "volume": message.velocity,
                    "channel": message.channel,
                    "value": message.note,
                    "start_time": cur_time
                })
                cur_delay = 0
            elif message.type == "note_off" or (message.type == "note_on" and message.velocity == 0):
                for i in range(len(track_notes)):
                    if track_notes[i]["duration"] is None and message.note == track_notes[i]["value"]:
                        track_notes[i]["duration"] = cur_time - track_notes[i].pop("start_time")
        ## Note off all pending notes
        for i in range(len(track_notes)):
            if track_notes[i]["duration"] is None:
                track_notes[i]["duration"] = cur_time - track_notes[i].pop("start_time")
        if len(track_notes) > 0: NOTES.append(track_notes)
    # Apply speed
    for t in range(len(NOTES)):
        for i in range(len(NOTES[t])):
            NOTES[t][i]["delay"] /= speed
            NOTES[t][i]["duration"] /= speed

    return NOTES

## Audio Generator Functions
def AudioGen_LoadMIDI(path="Data/GeneratedAudio/generated_midi.mid"):
    '''
    Audio Generator - Load MIDI file
    '''
    MIDIAudio = MidiFile_Read(path)

    return MIDIAudio

def AudioGen_SaveMIDI(MIDIAudio, save_path="Data/GeneratedAudio/generated_midi.mid"):
    '''
    Audio Generator - Save MIDI file
    '''
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as output_file:
        MIDIAudio.writeFile(output_file)

# RunCode
# print(Chord_GetNotes_FromShorthand("Dk"))
# MIDIAudio = AudioGen_LoadMIDI("Data/GeneratedAudio/generated_midi.mid")
# MIDI_ExtractNotes(MIDIAudio)