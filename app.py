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


# UI Functions
def UI_LoadNotes():
    # Basic inputs
    USERINPUT_tempo = st.number_input("Tempo", min_value=1, value=120)
    # Common Parameters
    USERINPUT_CommonParams = json.loads(st.text_area(
        "Common Note Parameters", height=300,
        value=json.dumps({
            "channel": 0,
            "octave": 4,
            "delay": 1,
            "duration": 1,
            "volume": 100
        }, indent=8)
    ))
    # Notes
    USERINPUT_NotesLoadMethod = st.selectbox("Load Notes Method", [
        "Tracks, Chords, Keys",
        "JSON"
    ])
    USERINPUT_Notes = []
    if USERINPUT_NotesLoadMethod == "Tracks, Chords, Keys":
        USERINPUT_NotesKeys = st.text_area("Enter Code (Separated by commas, spaces or new lines) (Denote keys with a extra 'k' at the end)", height=300)
        USERINPUT_NotesKeys = USERINPUT_NotesKeys.replace(",", " ").replace("\n", " ").split()
        ## Form keys from chords
        USERINPUT_Notes = USERINPUT_NotesKeys
    else:
        USERINPUT_Notes = json.loads(st.text_area(
            "Notes", height=300,
            value=json.dumps([
                {
                    "note": ""
                }
            ], indent=8)
        ))
    ## Decompose notes to keys
    USERINPUT_Notes = LIBRARIES["PianoMusicGenerator"].Note_DecomposeNotesToKeys(USERINPUT_NotesKeys, common_params=USERINPUT_CommonParams)

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
    LIBRARIES["PianoMusicGenerator"].CHORDS = json.load(open(PATHS["chords"], "r"))
    LIBRARIES["PianoMusicGenerator"].TRACKS = json.load(open(PATHS["tracks"], "r"))

    # Load Inputs
    st.markdown("## Piano Info")
    st.markdown("### Keys")
    st.markdown("```\n" + ", ".join(LIBRARIES["PianoMusicGenerator"].AVAILABLE_NOTES) + "\n```")

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
    MIDIAudio = LIBRARIES["PianoMusicGenerator"].MIDI_AddTrack(
        NOTES, 
        track=0, start_time=0, 
        tempo=USERINPUT_Inputs["other_params"]["tempo"]
    )
    ## Create audio file
    LIBRARIES["PianoMusicGenerator"].AudioGen_SaveMIDI(MIDIAudio, save_path=PATHS["midi_save_path"])
    # Display Outputs
    st.markdown("## Piano Music")
    Utils_MIDI2WAV(PATHS["midi_save_path"], PATHS["wav_save_path"])
    st.audio(PATHS["wav_save_path"])
    
#############################################################################################################################
# Driver Code
if __name__ == "__main__":
    main()