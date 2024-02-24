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
    "midi_save_path": "Data/GeneratedAudio/generated_midi_{track}.mid",
    "wav_save_path": "Data/GeneratedAudio/generated_wav_{track}.wav",
    "chords": "Data/SoundCodes/chords.json",
    "tracks": "Data/SoundCodes/tracks.json",
    "temp": {
        "audio": "Data/Temp/audio_{track}.wav",
        "video": "Data/Temp/video_{track}.mp4",
        "midi": "Data/Temp/midi.mid"
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
            "range": [0.01, 2.0]
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
DISPLAY_INTERMEDIATE_INFO = True
VISUALISATION_SIZE = 512

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

# Streamlit Cached Functions
# @st.cache_data # Disabled since USERINPUT_MIDIFile cannot be cached
def CACHEDFUNC_MIDI_ExtractNotes(USERINPUT_MIDIFile, USERINPUT_ClipTime, USERINPUT_Speed):
    '''
    Streamlit Cached Function - MIDI - Extract Notes
    '''
    USERINPUT_InputTracks_Notes = LIBRARIES["MusicGenerator"]["Piano"].MIDI_ExtractNotes(
        USERINPUT_MIDIFile, clip_time=USERINPUT_ClipTime, speed=USERINPUT_Speed
    )

    return USERINPUT_InputTracks_Notes

@st.cache_data
def CACHEDFUNC_Note_DecomposeNotesToKeys(USERINPUT_Notes, USERINPUT_CommonParams):
    '''
    Streamlit Cached Function - Note - Decompose Notes to Keys
    '''
    USERINPUT_Notes = LIBRARIES["MusicGenerator"]["Piano"].Note_DecomposeNotesToKeys(USERINPUT_Notes, common_params=USERINPUT_CommonParams)

    return USERINPUT_Notes

@st.cache_data
def CACHEDFUNC_GenerateAudioTracksFromNotes(USERINPUT_Tracks_Inputs):
    '''
    Streamlit Cached Function -
    '''
    # Init
    TRACKS_DATA = {
        "notes": [],
        "audio_paths": [],
        "midi_audios": []
    }
    # Generate Audio From Notes
    TRACKS_WORKING = [True]*len(USERINPUT_Tracks_Inputs)
    MIDIAudio_Combined = LIBRARIES["MusicGenerator"]["Piano"].MIDIFile(len(USERINPUT_Tracks_Inputs))
    TRACK_COLS = st.columns(len(USERINPUT_Tracks_Inputs))
    for t in range(len(USERINPUT_Tracks_Inputs)):
        st_track = TRACK_COLS[t]
        USERINPUT_Inputs = USERINPUT_Tracks_Inputs[t]
        ## Resolve Notes
        NOTES = USERINPUT_Inputs["notes"]
        ## Add track
        MIDIAudio = LIBRARIES["MusicGenerator"]["Piano"].MIDI_AddTrack(
            NOTES, 
            track=0, start_time=0, 
            tempo=USERINPUT_Inputs["other_params"]["tempo"]
        )
        ## Create audio file
        try:
            LIBRARIES["MusicGenerator"]["Piano"].AudioGen_SaveMIDI(MIDIAudio, save_path=PATHS["midi_save_path"].format(track=t))
        except Exception as e:
            TRACKS_WORKING[t] = False
            st_track.error(e)
        if not TRACKS_WORKING[t]: continue
        ## Add track for combined
        MIDIAudio_Combined = LIBRARIES["MusicGenerator"]["Piano"].MIDI_AddTrack(
            NOTES, MIDIAudio=MIDIAudio_Combined, 
            track=t, start_time=0, 
            tempo=USERINPUT_Inputs["other_params"]["tempo"]
        )
        # Display Track Outputs
        st_track.markdown("## Track")
        audio_path = PATHS["wav_save_path"].format(track=t)
        Utils_MIDI2WAV(PATHS["midi_save_path"].format(track=t), audio_path)
        st_track.audio(audio_path)
        TRACKS_DATA["notes"].append(NOTES)
        TRACKS_DATA["audio_paths"].append(audio_path)
        TRACKS_DATA["midi_audios"].append(MIDIAudio)
    ## Merge tracks into one MIDI file
    # MIDIAudio_Combined = LIBRARIES["MusicGenerator"]["Piano"].MIDI_CombineMIDIAudios(TRACKS_DATA["midi_audios"])
    LIBRARIES["MusicGenerator"]["Piano"].AudioGen_SaveMIDI(MIDIAudio_Combined, save_path=PATHS["midi_save_path"].format(track="combined"))

    return TRACKS_DATA

# UI Functions
def UI_PianoInfo():
    st.markdown("## Piano Info")
    with st.expander("### Keys", expanded=True):
        st.markdown("```\n" + ", ".join(LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES) + "\n```")
    with st.expander("### Simple Note Code Rules"):
        st.markdown(f"""
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
    with st.expander("### Note Code Format", expanded=True):
        note_params_keys_format_text = "{note_name}," + ",".join(["{" + k + "}" for k in NOTE_PARAM_KEYS])
        st.markdown("```shell\n" + note_params_keys_format_text + "\n```")

def UI_ExtractNotesFromMIDIFile():
    '''
    UI - Extract notes from input MIDI file
    '''
    # Init
    USERINPUT_InputTracks_Notes = []
    # Load MIDI file
    USERINPUT_MIDIFile = st.file_uploader("Upload MIDI File", type="mid")
    if USERINPUT_MIDIFile is not None:
        ## Read MIDI
        os.makedirs(os.path.dirname(PATHS["temp"]["midi"]), exist_ok=True)
        open(PATHS["temp"]["midi"], "wb").write(USERINPUT_MIDIFile.read())
        USERINPUT_MIDIFile = LIBRARIES["MusicGenerator"]["Piano"].AudioGen_LoadMIDI(PATHS["temp"]["midi"])
        ## Speed
        USERINPUT_Speed = st.number_input("Speed", min_value=0.01, value=1.0)
        ## Clip and Extract Notes
        cols = st.columns(2)
        cols = [cols[0].columns((1, 3)), cols[1].columns((1, 3))]
        AUDIO_ClipTime = [0.0, float(USERINPUT_MIDIFile.length)]
        USERINPUT_ClipTime = [-1, -1]
        USERINPUT_ClipCheck = [
            cols[0][0].checkbox("Clip Start", key="clip_time_start_checkbox"),
            cols[1][0].checkbox("Clip End", key="clip_time_end_checkbox")
        ]
        if USERINPUT_ClipCheck[0]:
            USERINPUT_ClipTime[0] = cols[0][1].number_input(
                "", min_value=AUDIO_ClipTime[0], max_value=AUDIO_ClipTime[1], value=AUDIO_ClipTime[0],
                key="clip_time_start_number_input"
            )
        if USERINPUT_ClipCheck[1]:
            USERINPUT_ClipTime[1] = cols[1][1].number_input(
                "", min_value=max(AUDIO_ClipTime[0], USERINPUT_ClipTime[0]), max_value=AUDIO_ClipTime[1],
                value=AUDIO_ClipTime[1], key="clip_time_end_number_input"
            )
        Display_ClipTime = (
            USERINPUT_ClipTime[0] if USERINPUT_ClipTime[0] > -1 else AUDIO_ClipTime[0],
            USERINPUT_ClipTime[1] if USERINPUT_ClipTime[1] > -1 else AUDIO_ClipTime[1]
        )
        st.slider("Clip", min_value=AUDIO_ClipTime[0], max_value=AUDIO_ClipTime[1], value=Display_ClipTime, disabled=True)
        USERINPUT_InputTracks_Notes = CACHEDFUNC_MIDI_ExtractNotes(USERINPUT_MIDIFile, USERINPUT_ClipTime, USERINPUT_Speed)

    return USERINPUT_InputTracks_Notes

def UI_LoadNotes(USERINPUT_Tracks_Notes=[], editable=False):
    '''
    UI - Load Notes
    '''
    # Basic inputs
    USERINPUT_tempo = st.number_input("Tempo", min_value=1, value=60, disabled=True)
    USERINPUT_NTracks = st.number_input("Tracks", min_value=1, value=max(1, len(USERINPUT_Tracks_Notes)), disabled=not editable)
    OUT = []
    # Iterate over tracks
    TRACK_COLS = st.columns(USERINPUT_NTracks)
    for t in range(USERINPUT_NTracks):
        st_track = TRACK_COLS[t]
        USERINPUT_Notes = USERINPUT_Tracks_Notes[t] if t < len(USERINPUT_Tracks_Notes) else None
        # Common Parameters
        USERINPUT_CommonParams = json.loads(st_track.text_area(
            "Common Note Parameters", height=300,
            value=json.dumps(LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["common_params"], indent=8),
            key=f"CommonParams_{t}"
        ))
        # Notes
        if USERINPUT_Notes is None:
            USERINPUT_NotesLoadMethod = st_track.selectbox(
                "Load Notes Method", 
                ["Simple Note Code", "JSON"],
                key=f"NotesLoadMethod_{t}"
            )
            USERINPUT_Notes = []
            if USERINPUT_NotesLoadMethod == "Simple Note Code":
                DefaultNotesCode = "\n".join([NoteCode_GetNoteCode(note) for note in LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["notes"]])
                USERINPUT_NotesKeys = st_track.text_area(
                    "Enter Code", height=300,
                    value=DefaultNotesCode,
                    key=f"NotesKeys_{t}"
                )
                USERINPUT_Notes = USERINPUT_NotesKeys.replace("\n", " ").split()
                USERINPUT_Notes = [NoteCode_Parse(note) for note in USERINPUT_Notes]
            else:
                USERINPUT_Notes = json.loads(st_track.text_area(
                    "Notes", height=300,
                    value=json.dumps(LIBRARIES["MusicGenerator"]["Piano"].TRACKS["default"]["notes"], indent=8),
                    key=f"Notes_{t}"
                ))
        ## Display Notes JSON
        st_track.markdown(f"Input Notes ({len(USERINPUT_Notes)})")
        if DISPLAY_INTERMEDIATE_INFO: st_track.json(USERINPUT_Notes, expanded=False)
        ## Decompose notes to keys
        USERINPUT_Notes = CACHEDFUNC_Note_DecomposeNotesToKeys(USERINPUT_Notes, USERINPUT_CommonParams)
        ## Display Notes JSON
        st_track.markdown(f"Decomposed Notes ({len(USERINPUT_Notes)})")
        if DISPLAY_INTERMEDIATE_INFO: st_track.json(USERINPUT_Notes, expanded=False)
        ## Display notes MIDI as Plot
        NOTE_VALUE_RANGE = LIBRARIES["MusicGenerator"]["Piano"].NOTE_VALUE_RANGE
        AVAILABLE_NOTES = LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES
        NOTE_VALUE_NAME_MAP = {
            v: AVAILABLE_NOTES[((v-NOTE_VALUE_RANGE[0]) % len(AVAILABLE_NOTES))]
            for v in range(NOTE_VALUE_RANGE[0], NOTE_VALUE_RANGE[1]+1)
        }
        USERINPUT_Notes_KnownOnly = [note for note in USERINPUT_Notes if note["value"] >= 0]
        MIDI_FIG = LIBRARIES["Visualisers"]["MIDIPlot"].MIDIPlot_PlotNotes_HBar(USERINPUT_Notes_KnownOnly, note_value_name_map=NOTE_VALUE_NAME_MAP)
        st_track.pyplot(MIDI_FIG)
        TRACK_OUT = {
            "other_params": {
                "tempo": USERINPUT_tempo
            },
            "notes": USERINPUT_Notes
        }
        # print("\n\nTRACK", t, ":", json.dumps(OUT, indent=4), "\n\n")
        OUT.append(TRACK_OUT)

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
        PROB_DIST = {n: 1 for n in POSSIBLE_NOTES}
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
                    options_prob_dist = {str(n): 1 for n in POSSIBLE_OPTIONS}
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

def UI_NoteVisualiser(TRACKS_NOTES, TRACKS_audio_paths):
    '''
    UI - Note Visualiser
    '''
    global VISUALISATION_SIZE
    # Prereq
    VISUALISATION_SIZE = st.sidebar.number_input("Visualisation Size", min_value=128, max_value=1024, value=512, step=128)
    # Init
    UNIQUE_NOTES = LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES
    TRACKS_NOTES = [[dict(n) for n in TRACKS_NOTES[t]] for t in range(len(TRACKS_NOTES))]
    # Visualise
    USERINPUT_VisType = st.selectbox("Select Visualiser", ["Circle Bouncer", "None"])
    if USERINPUT_VisType == "Circle Bouncer":
        # Params
        USERINPUT_VisMode = st.selectbox("Mode", ["Line Sequence", "Converge Lines"])
        USERINPUT_VisMode = USERINPUT_VisMode.replace(" ", "_").lower()
        cols = st.columns(3)
        USERINPUT_UsedNotesOnly = cols[0].checkbox("Visualise used notes only", value=False)
        USERINPUT_OnlyNoteNames = cols[1].checkbox("Visualise without octaves", value=True)
        if not USERINPUT_OnlyNoteNames: USERINPUT_GroupNoteNames = cols[2].checkbox("Group by note names", value=True)
        ## Update based on params
        if not USERINPUT_OnlyNoteNames:
            AVAILABLE_NOTES = LIBRARIES["MusicGenerator"]["Piano"].AVAILABLE_NOTES
            NOTE_VALUE_RANGE = LIBRARIES["MusicGenerator"]["Piano"].NOTE_VALUE_RANGE
            OCTAVES = LIBRARIES["MusicGenerator"]["Piano"].OCTAVES
            NOTE_OCTAVE_SEPARATOR = ""
            if not USERINPUT_GroupNoteNames:
                UNIQUE_NOTES = [
                    str(UNIQUE_NOTES[v%len(AVAILABLE_NOTES)]) + NOTE_OCTAVE_SEPARATOR + str(v//len(AVAILABLE_NOTES))
                    for v in range(NOTE_VALUE_RANGE[0], NOTE_VALUE_RANGE[1]+1)
                ]
            else:
                UNIQUE_NOTES = []
                for ni in range(len(AVAILABLE_NOTES)):
                    UNIQUE_NOTES.extend([AVAILABLE_NOTES[ni] + NOTE_OCTAVE_SEPARATOR + str(oi) for oi in OCTAVES])
            for t in range(len(TRACKS_NOTES)):
                for ni in range(len(TRACKS_NOTES[t])):
                    TRACKS_NOTES[t][ni]["note"] = TRACKS_NOTES[t][ni]["note"] + NOTE_OCTAVE_SEPARATOR + str(TRACKS_NOTES[t][ni]["octave"])
        ## Check used notes only
        if USERINPUT_UsedNotesOnly:
            UNIQUE_NOTES_Used = []
            USED_NOTES = []
            for t in range(len(TRACKS_NOTES)):
                USED_NOTES.extend(list(set([n["note"] for n in TRACKS_NOTES[t]])))
                USED_NOTES = list(set(USED_NOTES))
            for un in UNIQUE_NOTES:
                if un in USED_NOTES: UNIQUE_NOTES_Used.append(un)
            UNIQUE_NOTES = USED_NOTES
        # Other Params
        cols = st.columns(3)
        USERINPUT_ShowText = cols[0].checkbox("Mark Notes", value=True)
        USERINPUT_FillCircle = cols[1].checkbox("Fill Circle", value=False)
        USERINPUT_FPNS = cols[2].number_input("Frames per note second", min_value=1, value=24)
        cols = st.columns(2)
        USERINPUT_Colors = {
            "circle": cols[0].color_picker("Circle Color", "#FFFFFF"),
            "note": {
                "cmap": cols[1].selectbox(
                    "Notes Colormap", 
                    LIBRARIES["Visualisers"]["CircleBouncer"].CMAPS, 
                    index=LIBRARIES["Visualisers"]["CircleBouncer"].CMAPS.index(LIBRARIES["Visualisers"]["CircleBouncer"].CMAP_DEFAULT)
                )
            }
        }
        cols = st.columns(2)
        USERINPUT_FadeParams = {
            "type": cols[0].selectbox("Fade Type", ["None", "Linear"]).replace(" ", "_").lower(),
            "threshold": -1
        }
        if USERINPUT_FadeParams["type"] != "none":
            USERINPUT_FadeParams["threshold"] = cols[1].number_input("Displayed Notes Window", min_value=1, value=5)
        else:
            subcols = cols[1].columns(2)
            if subcols[0].checkbox("Apply Threshold", value=False):
                USERINPUT_FadeParams["threshold"] = subcols[1].number_input("Displayed Notes Window", min_value=1, value=5)
        USERINPUT_CompressSize = st.checkbox("Compress Combined Video Size", value=True)
        # Process Check
        USERINPUT_Process = st.checkbox("Stream Visualise", value=False)
        if not USERINPUT_Process: USERINPUT_Process = st.button("Visualise")
        if not USERINPUT_Process: st.stop()
        # Visualise
        TRACKS_DATA = {
            "video_paths": []
        }
        TRACK_COLS = st.columns(len(TRACKS_NOTES))
        for t in range(len(TRACKS_NOTES)):
            st_track = TRACK_COLS[t]
            audio_path = TRACKS_audio_paths[t]
            NOTES = TRACKS_NOTES[t]
            # ## Clean chords (notes with delay 0 causing visualisation jumps) (NOT WORKING, VIDEO DURATION IS MORE THAN AUDIO AND NOT INSYNC)
            # NOTES_CLEANED = []
            # for ni in range(len(NOTES)):
            #     note = NOTES[ni]
            #     if ni > 0 and note["delay"] == 0:
            #         if note["duration"] > NOTES_CLEANED[-1]["duration"]:
            #             NOTES_CLEANED[-1] = note
            #     else:
            #         NOTES_CLEANED.append(note)
            # NOTES = NOTES_CLEANED
            ## Generate Frames
            NOTES_FRAMES = LIBRARIES["Visualisers"]["CircleBouncer"].CircleBouncer_VisualiseNotes(
                NOTES, UNIQUE_NOTES, frame_size=(VISUALISATION_SIZE, VISUALISATION_SIZE),
                mode=USERINPUT_VisMode,
                show_text=USERINPUT_ShowText, frames_per_notesec=USERINPUT_FPNS,
                fade_params=USERINPUT_FadeParams,
                colors=USERINPUT_Colors,
                sizes={
                    "gap": 0.1,
                    "circle": {
                        "thickness": 0.0025 if not USERINPUT_FillCircle else -1
                    },
                    "text": {
                        "scale": 0.0005 if not USERINPUT_OnlyNoteNames else 0.001
                    },
                    "line": {
                        "thickness": 0.0025
                    },
                    "point": {
                        "radius": 0.01
                    }
                }
            )
            video_path = PATHS["temp"]["video"].format(track=t)
            LIBRARIES["Visualisers"]["CircleBouncer"].VideoUtils_SaveVisualisationVideo(
                NOTES, NOTES_FRAMES, audio_path, video_path
            )
            st_track.video(video_path)
            TRACKS_DATA["video_paths"].append(video_path)
        # Combine Visualisations
        video_path_combined = PATHS["temp"]["video"].format(track="combined")
        LIBRARIES["Visualisers"]["CircleBouncer"].VideoUtils_CombineVisualisationVideos(
            TRACKS_DATA["video_paths"],
            video_path_combined,
            compress_size=USERINPUT_CompressSize
        )
        st.video(video_path_combined)
    else:
        pass

# Repo Based Functions
def basic_piano_sequencer():
    global DISPLAY_INTERMEDIATE_INFO
    # Title
    st.header("Basic Piano Sequencer")

    # Prereq Loaders
    LIBRARIES["MusicGenerator"]["Piano"].CHORDS = json.load(open(PATHS["chords"], "r"))
    LIBRARIES["MusicGenerator"]["Piano"].TRACKS = json.load(open(PATHS["tracks"], "r"))
    DISPLAY_INTERMEDIATE_INFO = st.sidebar.checkbox("Display Intermediate Info", value=True)

    # Load Inputs
    UI_PianoInfo()
    st.markdown("## Inputs")
    USERINPUT_InputTracks_Notes = UI_ExtractNotesFromMIDIFile()
    if DISPLAY_INTERMEDIATE_INFO: st.json(USERINPUT_InputTracks_Notes)
    USERINPUT_Process = st.checkbox("Finalise Input Clip", value=False)
    if not USERINPUT_Process: st.stop()
    ## Load Notes
    USERINPUT_Tracks_Inputs = UI_LoadNotes(USERINPUT_InputTracks_Notes, editable=True)

    # Process Check
    USERINPUT_Process = st.checkbox("Stream Process", value=False)
    if not USERINPUT_Process: USERINPUT_Process = st.button("Process")
    if not USERINPUT_Process: st.stop()
    # Process Inputs
    TRACKS_DATA = CACHEDFUNC_GenerateAudioTracksFromNotes(USERINPUT_Tracks_Inputs)
    # Display Outputs
    st.markdown("## Piano Music")
    audio_path_combined = PATHS["wav_save_path"].format(track="combined")
    Utils_MIDI2WAV(PATHS["midi_save_path"].format(track="combined"), audio_path_combined)
    st.audio(audio_path_combined)
    # Visualise Outputs
    st.markdown("## Visualisations")
    UI_NoteVisualiser(
        TRACKS_DATA["notes"], TRACKS_DATA["audio_paths"]
    )

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
    UI_PianoInfo()
    st.markdown("## Inputs")
    ## Notes Count
    USERINPUT_NotesCount = st.number_input("Number of Notes", min_value=1, value=5)
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
    TRACKS_NOTES = [NOTES]
    USERINPUT_Inputs = UI_LoadNotes(TRACKS_NOTES, editable=False)
    USERINPUT_Inputs = USERINPUT_Inputs[0]

    # Process Check
    USERINPUT_Process = st.checkbox("Stream Process", value=False)
    if not USERINPUT_Process: USERINPUT_Process = st.button("Process")
    if not USERINPUT_Process: st.stop()
    # Process Inputs

    # ## Resolve Notes
    # NOTES = USERINPUT_Inputs["notes"]
    # ## Add track
    # MIDIAudio = LIBRARIES["MusicGenerator"]["Piano"].MIDI_AddTrack(
    #     NOTES, 
    #     track=0, start_time=0, 
    #     tempo=USERINPUT_Inputs["other_params"]["tempo"]
    # )
    # ## Create audio file
    # LIBRARIES["MusicGenerator"]["Piano"].AudioGen_SaveMIDI(MIDIAudio, save_path=PATHS["midi_save_path"])

    TRACKS_DATA = CACHEDFUNC_GenerateAudioTracksFromNotes([USERINPUT_Inputs])

    # Display Outputs
    st.markdown("## Generated Piano Music")
    audio_path_combined = PATHS["wav_save_path"].format(track="combined")
    Utils_MIDI2WAV(PATHS["midi_save_path"].format(track="combined"), audio_path_combined)
    st.audio(audio_path_combined)
    # Visualise Outputs
    st.markdown("## Visualisations")
    UI_NoteVisualiser(
        TRACKS_DATA["notes"], TRACKS_DATA["audio_paths"]
    )
    
#############################################################################################################################
# Driver Code
if __name__ == "__main__":
    main()