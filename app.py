"""
Stream lit GUI for hosting MusicVis
"""

# Imports
import os
import av
import json
import functools
import streamlit as st
import matplotlib.pyplot as plt

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
    "tracks": "Data/SoundCodes/tracks.json",
    "temp": {
        "audio": "Data/Temp/audio.wav",
        "video": "Data/Temp/video.mp4"
    }
}

# Util Vars
CACHE = {}
NOTE_PARAMS_INFO = {
    "delay": {
        "type": float,
        "gen_data": {
            "type": "number",
            "range": [0.0, 2.0]
        }
    },
    "duration": {
        "type": float,
        "gen_data": {
            "type": "number",
            "range": [0.0, 2.0]
        }
    },
    "octave": {
        "type": float,
        "gen_data": {
            "type": "selection",
            "options": LIBRARIES["MusicGenerator"]["Piano"].OCTAVES
        }
    }, 
    "volume": {
        "type": float
    },
    "channel": {
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
def UI_LoadNotes(USERINPUT_Notes=None):
    '''
    UI - Load Notes
    '''
    # Basic inputs
    USERINPUT_tempo = st.number_input("Tempo", min_value=1, value=60)
    # Common Parameters
    USERINPUT_CommonParams = json.loads(st.text_area(
        "Common Note Parameters", height=300,
        value=json.dumps(LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["common_params"], indent=8)
    ))
    # Notes
    if USERINPUT_Notes is None:
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
    ## Display Notes JSON
    st.markdown(f"Input Notes ({len(USERINPUT_Notes)})")
    st.json(USERINPUT_Notes, expanded=False)
    ## Decompose notes to keys
    USERINPUT_Notes = LIBRARIES["MusicGenerator"]["Piano"].Note_DecomposeNotesToKeys(USERINPUT_Notes, common_params=USERINPUT_CommonParams)
    ## Display Notes JSON
    st.markdown(f"Decomposed Notes ({len(USERINPUT_Notes)})")
    st.json(USERINPUT_Notes, expanded=False)
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

def UI_NoteGenerator_RandomSequence_LoadEnvUpdateFunc(POSSIBLE_NOTES):
    '''
    UI - Note Generator - Random Sequence - Load Environment Update Function
    '''
    # Select function
    USERINPUT_EnvUpdateFuncName = st.selectbox("Select Update Function", LIBRARIES["NoteGenerator"]["RandomSequence"].NOTEGENENV_UPDATE_FUNCS.keys())
    USERINPUT_EnvUpdateFunc = LIBRARIES["NoteGenerator"]["RandomSequence"].NOTEGENENV_UPDATE_FUNCS[USERINPUT_EnvUpdateFuncName]
    # Enter params
    if USERINPUT_EnvUpdateFuncName == "Constant Random Distribution":
        ## Get Probability Distribution
        PROB_DIST = {n: round(1.0/len(POSSIBLE_NOTES), 2) for n in POSSIBLE_NOTES}
        PROB_DIST = json.loads(st.text_area(
            "Enter probability distribution", height=300,
            value=json.dumps(PROB_DIST, indent=8)
        ))
        POSSIBLE_NOTES = list(PROB_DIST.keys())
        ## Normalise the probability distribution
        TOTAL_PROB = sum([PROB_DIST[n] for n in PROB_DIST.keys()])
        PROB_DIST = {n: round(PROB_DIST[n]/TOTAL_PROB, 2) for n in PROB_DIST.keys()}
        ## Display Probability Distribution
        FIG_PROB_DIST = plt.figure()
        plt.pie(np.array([PROB_DIST[n] for n in POSSIBLE_NOTES]), labels=[n + f" ({PROB_DIST[n]})" for n in POSSIBLE_NOTES])
        plt.close()
        st.pyplot(FIG_PROB_DIST)
        ## Get Parameters Gen Data
        PARAMS_GEN_DATA = {}
        for pk in NOTE_PARAMS_INFO.keys():
            if "gen_data" in NOTE_PARAMS_INFO[pk].keys():
                if NOTE_PARAMS_INFO[pk]["gen_data"]["type"] == "number":
                    val_range = NOTE_PARAMS_INFO[pk]["gen_data"]["range"]
                    cols = st.columns(2)
                    PARAMS_GEN_DATA[pk] = {
                        "type": "number",
                        "range": [
                            cols[0].number_input(f"{pk} min", value=val_range[0]), cols[1].number_input(f"{pk} max", value=val_range[1])
                        ]
                    }
                elif NOTE_PARAMS_INFO[pk]["gen_data"]["type"] == "selection":
                    POSSIBLE_OPTIONS = NOTE_PARAMS_INFO[pk]["gen_data"]["options"]
                    options_prob_dist = {str(n): round(1.0/len(POSSIBLE_OPTIONS), 2) for n in POSSIBLE_OPTIONS}
                    options_prob_dist = json.loads(st.text_area(
                        f"{pk} probability distribution", height=300,
                        value=json.dumps(options_prob_dist, indent=8)
                    ))
                    for n in POSSIBLE_OPTIONS:
                        if str(n) not in options_prob_dist.keys(): options_prob_dist[str(n)] = 0.0
                    ### Normalise the probability distribution
                    options_total_prob = sum([options_prob_dist[n] for n in options_prob_dist.keys()])
                    options_prob_dist = [round(options_prob_dist[str(n)]/options_total_prob, 2) for n in POSSIBLE_OPTIONS]
                    ## Display Probability Distribution
                    FIG_options_prob_dist = plt.figure()
                    plt.pie(np.array([options_prob_dist[i] for i in range(len(POSSIBLE_OPTIONS))]), labels=[str(POSSIBLE_OPTIONS[i]) + f" ({options_prob_dist[i]})" for i in range(len(POSSIBLE_OPTIONS))])
                    plt.close()
                    st.pyplot(FIG_options_prob_dist)
                    ### Form gen data
                    PARAMS_GEN_DATA[pk] = {
                        "type": "selection",
                        "options": POSSIBLE_OPTIONS,
                        "prob": options_prob_dist
                    }
                else:
                    PARAMS_GEN_DATA[pk] = NOTE_PARAMS_INFO[pk]["gen_data"]
        VALUE_GEN_MAP = {}
        for i in range(len(POSSIBLE_NOTES)):
            VALUE_GEN_MAP[i] = {
                "prob": PROB_DIST[POSSIBLE_NOTES[i]],
                "params": PARAMS_GEN_DATA
            }
        USERINPUT_EnvUpdateFunc = functools.partial(USERINPUT_EnvUpdateFunc, VALUE_GEN_MAP=VALUE_GEN_MAP)
    
    return USERINPUT_EnvUpdateFunc

def UI_NoteVisualiser(NOTES, UNIQUE_NOTES, audio_path):
    '''
    UI - Note Visualiser
    '''
    USERINPUT_VisType = st.selectbox("Select Visualiser", ["None", "Circle Bouncer"])
    if USERINPUT_VisType == "Circle Bouncer":
        # Params
        USERINPUT_ShowText = st.checkbox("Show Notes", value=True)
        cols = st.columns(4)
        USERINPUT_Colors = {
            "circle": cols[0].color_picker("Circle Color", "#85FFE9"),
            "text": cols[1].color_picker("Text Color", "#2DCC61"),
            "line": cols[2].color_picker("Line Color", "#FF7373"),
            "point": cols[3].color_picker("Point Color", "#DE2828")
        }
        # Process Check
        USERINPUT_Process = st.checkbox("Stream Visualise", value=False)
        if not USERINPUT_Process: USERINPUT_Process = st.button("Visualise")
        if not USERINPUT_Process: st.stop()
        # Visualise
        NOTES_FRAMES = LIBRARIES["Visualisers"]["CircleBouncer"].CircleBouncer_VisualiseNotes(
            NOTES, UNIQUE_NOTES, show_text=USERINPUT_ShowText
        )
        LIBRARIES["Visualisers"]["CircleBouncer"].VideoUtils_SaveVisualisationVideo(
            NOTES, NOTES_FRAMES, audio_path, PATHS["temp"]["video"]
        )
        st.video(PATHS["temp"]["video"])
    else:
        pass

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

def piano_music_generator():
    # Title
    st.header("Piano Music Generator")

    # Prereq Loaders
    LIBRARIES["MusicGenerator"]["Piano"].CHORDS = json.load(open(PATHS["chords"], "r"))
    LIBRARIES["MusicGenerator"]["Piano"].TRACKS = json.load(open(PATHS["tracks"], "r"))
    ## Possible Notes and Maps
    POSSIBLE_NOTES = list(LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES)
    POSSIBLE_NOTES += ["_" + c for c in LIBRARIES["MusicGenerator"]["Piano"].CHORDS.keys()]
    POSSIBLE_NOTES += list(LIBRARIES["MusicGenerator"]["Piano"].TRACKS.keys())
    MAPS = {
        "name_value": {},
        "value_name": {}
    }
    for i in range(len(POSSIBLE_NOTES)):
        MAPS["name_value"][POSSIBLE_NOTES[i]] = i
        MAPS["value_name"][i] = POSSIBLE_NOTES[i]

    # Load Inputs
    st.markdown("## Piano Info")
    st.markdown("### Keys")
    st.markdown("```\n" + ", ".join(LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES) + "\n```")

    st.markdown("## Inputs")
    ## Notes Count
    USERINPUT_NotesCount = st.number_input("Number of Notes", 1, 100, 5)
    ## Select Generator Type
    USERINPUT_NoteGenType = st.sidebar.selectbox("Select Note Generator", list(LIBRARIES["NoteGenerator"].keys()))
    if USERINPUT_NoteGenType == "RandomSequence":
        USERINPUT_EnvUpdateFunc = UI_NoteGenerator_RandomSequence_LoadEnvUpdateFunc(POSSIBLE_NOTES)
        USERINPUT_Seed = st.number_input("Seed", 0, 1000, 1)
        USERINPUT_NoteGenFunc = functools.partial(
            LIBRARIES["NoteGenerator"]["RandomSequence"].RandomSequence_GenerateNotes,
            ENV_UPDATE_FUNC=USERINPUT_EnvUpdateFunc,
            MAPS=MAPS,
            seed=USERINPUT_Seed,
            PREV_NOTES=[]
        )
    else:
        pass

    # Process Check
    USERINPUT_Generate = st.checkbox("Stream Generate", value=True)
    if not USERINPUT_Generate: USERINPUT_Generate = st.button("Generate")
    if not USERINPUT_Generate: st.stop()
    ## Generate Notes
    NOTES_DATA = USERINPUT_NoteGenFunc(USERINPUT_NotesCount)
    NOTES = NOTES_DATA["notes"]
    USERINPUT_Inputs = UI_LoadNotes(NOTES)

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
    # Visualise Outputs
    st.markdown("## Visualisations")
    UI_NoteVisualiser(NOTES, LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES, PATHS["wav_save_path"])
    
#############################################################################################################################
# Driver Code
if __name__ == "__main__":
    main()