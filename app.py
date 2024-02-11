"""
Stream lit GUI for hosting MusicVis
"""

# Imports
import os
import json
import streamlit as st

from MusicVis import *

# Main Vars
config = json.load(open("./StreamLitGUI/UIConfig.json", "r"))

# Main Functions
def main():
    # Create Sidebar
    selected_box = st.sidebar.selectbox(
    "Choose one of the following",
        tuple(
            [config["PROJECT_NAME"]] + 
            config["PROJECT_MODES"]
        )
    )
    
    if selected_box == config["PROJECT_NAME"]:
        HomePage()
    else:
        correspondingFuncName = selected_box.replace(" ", "_").lower()
        if correspondingFuncName in globals().keys():
            globals()[correspondingFuncName]()
 

def HomePage():
    st.title(config["PROJECT_NAME"])
    st.markdown("Github Repo: " + "[" + config["PROJECT_LINK"] + "](" + config["PROJECT_LINK"] + ")")
    st.markdown(config["PROJECT_DESC"])
    # st.write(open(config["PROJECT_README"], "r").read())

#############################################################################################################################
# Repo Based Vars
PATHS = {
    "cache": "StreamLitGUI/CacheData/Cache.json",
    "midi_save_path": "Data/GeneratedAudio/generated_midi.mid",
    "wav_save_path": "Data/GeneratedAudio/generated_wav.wav",
    "chords": "Data/SoundCodes/chords.json",
    "tracks": "Data/SoundCodes/tracks.json"
}

# Util Vars
CACHE = {}
NOTE_PARAMS_INFO = {
    "channel": {
        "type": float
    }, 
    "octave": {
        "type": float
    }, 
    "delay": {
        "type": float
    }, 
    "duration": {
        "type": float
    }, 
    "volume": {
        "type": float
    }
}
NOTE_PARAM_KEYS = list(NOTE_PARAMS_INFO.keys())

# Util Functions
def LoadCache():
    '''
    Load Cache
    '''
    global CACHE
    CACHE = json.load(open(PATHS["cache"], "r"))

def SaveCache():
    '''
    Save Cache
    '''
    global CACHE
    json.dump(CACHE, open(PATHS["cache"], "w"), indent=4)

# Main Functions
def NoteCode_Parse(note_code):
    '''
    Note Code - Convert note code to note object
    '''
    # Remove spaces
    note_code = note_code.strip().replace(" ", "")
    # Parse
    note_data = note_code.split(",")
    # Required parameters
    note = {"note": note_data[0]}
    # Optional parameters
    for i in range(min(len(note_data)-1, len(NOTE_PARAM_KEYS))):
        if note_data[i+1] not in ["", "?"]: note[NOTE_PARAM_KEYS[i]] = note_data[i+1]
    # Convert parameters to proper types
    for k in NOTE_PARAM_KEYS:
        if k not in note.keys(): continue
        note[k] = NOTE_PARAMS_INFO[k]["type"](note[k])
        ## Special cases
        ### Convert float to int if decimal part is 0
        if NOTE_PARAMS_INFO[k]["type"] == float:
            if note[k] - int(note[k]) == 0.0:
                note[k] = int(note[k])

    return note

def NoteCode_GetNoteCode(note):
    '''
    Note Code - Convert note object to note code
    '''
    # If note object is string, return itself
    if type(note) == str: return str(note)
    # Form note code
    note_code = note["note"]
    params_code = ",".join([str(note[k]) if k in note.keys() else "?" for k in NOTE_PARAM_KEYS])
    if not (params_code == ""): note_code = note_code + "," + params_code

    return note_code

# UI Functions
def UI_LoadNotes():
    # Basic inputs
    USERINPUT_tempo = st.number_input("Tempo", min_value=1, value=120)
    # Common Parameters
    USERINPUT_CommonParams = json.loads(st.text_area(
        "Common Note Parameters", height=300,
        value=json.dumps(LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["common_params"], indent=8)
    ))
    # Notes
    USERINPUT_NotesLoadMethod = st.selectbox("Load Notes Method", [
        "Simple Note Code",
        "JSON"
    ])
    USERINPUT_Notes = []
    if USERINPUT_NotesLoadMethod == "Simple Note Code":
        st.markdown(f"""
        #### Simple Note Code Rules
        - Notes can be separated only by spaces or new lines (" " or "\\n")
        - Note is given followed by its parameters all separated by commas (",") only
            - Order of parameters is {NOTE_PARAM_KEYS}
            - If you dont want to specify any parameter, simply specify the value as "?"
                - It will be replaced with the value specified in the common parameters
            - Eg. _C,?,?,2,2,?
                - C is the chord
                - delay is 2
                - duration is 2
                - Other parameters are from common parameters
        - You can not give the commas also and the further missing parameters are specified from common parameters
            - Eg. _C,1
                - C is the chord
                - channel is 1
                - All other parameters are from common parameters
        """)
        note_params_keys_format_text = "{note_name}," + ",".join(["{" + k + "}" for k in NOTE_PARAM_KEYS])
        st.markdown("Note Code Format:")
        st.markdown("```shell\n" + note_params_keys_format_text + "\n```")
        DefaultNotesCode = "\n".join([NoteCode_GetNoteCode(note) for note in LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["notes"]])
        USERINPUT_NotesKeys = st.text_area(
            "Enter Code", height=300,
            value=DefaultNotesCode
        )
        USERINPUT_Notes = USERINPUT_NotesKeys.replace("\n", " ").split()
        USERINPUT_Notes = [NoteCode_Parse(note) for note in USERINPUT_Notes]
    else:
        USERINPUT_Notes = json.loads(st.text_area(
            "Notes", height=300,
            value=json.dumps(LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["notes"], indent=8)
        ))
    ## Decompose notes to keys
    USERINPUT_Notes = LIBRARIES["MusicGenerator"]["Piano"].Note_DecomposeNotesToKeys(USERINPUT_Notes, common_params=USERINPUT_CommonParams)
    ## Display notes MIDI as Plot
    NOTE_VALUE_NAME_MAP = {
        v: LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES[((v-LIBRARIES["MusicGenerator"]["Piano"].NOTE_VALUE_RANGE[0]) % LIBRARIES["MusicGenerator"]["Piano"].NOTES_IN_OCTAVE)]
        for v in range(LIBRARIES["MusicGenerator"]["Piano"].NOTE_VALUE_RANGE[0], LIBRARIES["MusicGenerator"]["Piano"].NOTE_VALUE_RANGE[1]+1)
    }
    USERINPUT_Notes_KnownOnly = [note for note in USERINPUT_Notes if note["value"] >= 0]
    MIDI_FIG = LIBRARIES["Visualisers"]["MIDIPlot"].MIDIPlot_PlotNotes_HBar(USERINPUT_Notes_KnownOnly, note_value_name_map=NOTE_VALUE_NAME_MAP)
    st.pyplot(MIDI_FIG)

    OUT = {
        "other_params": {
            "tempo": USERINPUT_tempo
        },
        "notes": USERINPUT_Notes
    }
    # print("\n\n", json.dumps(OUT, indent=4), "\n\n")
    return OUT

# Repo Based Functions
def basic_piano_sequencer():
    # Title
    st.header("Basic Piano Sequencer")

    # Prereq Loaders
    LIBRARIES["MusicGenerator"]["Piano"].CHORDS = json.load(open(PATHS["chords"], "r"))
    LIBRARIES["MusicGenerator"]["Piano"].TRACKS = json.load(open(PATHS["tracks"], "r"))

    # Load Inputs
    st.markdown("## Piano Info")
    st.markdown("### Keys")
    st.markdown("```\n" + ", ".join(LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES) + "\n```")

    st.markdown("## Inputs")
    USERINPUT_Inputs = UI_LoadNotes()

    # Process Check
    USERINPUT_Process = st.checkbox("Stream Process", value=False)
    if not USERINPUT_Process: USERINPUT_Process = st.button("Process")
    if not USERINPUT_Process: st.stop()
    # Process Inputs
    ## Resolve Notes
    NOTES = USERINPUT_Inputs["notes"]
    ## Add track
    MIDIAudio = LIBRARIES["MusicGenerator"]["Piano"].MIDI_AddTrack(
        NOTES, 
        track=0, start_time=0, 
        tempo=USERINPUT_Inputs["other_params"]["tempo"]
    )
    ## Create audio file
    LIBRARIES["MusicGenerator"]["Piano"].AudioGen_SaveMIDI(MIDIAudio, save_path=PATHS["midi_save_path"])
    # Display Outputs
    st.markdown("## Piano Music")
    Utils_MIDI2WAV(PATHS["midi_save_path"], PATHS["wav_save_path"])
    st.audio(PATHS["wav_save_path"])
    
#############################################################################################################################
# Driver Code
if __name__ == "__main__":
    main()