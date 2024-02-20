"""
Visualiser Library - Circle Bouncer
"""

# Imports
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, clips_array

# Main Vars
CMAPS = sorted(list(plt.cm._colormaps))
CMAP_DEFAULT = "rainbow"

# Util Functions
def Util_Hex2RGB(hex):
    '''
    Util - Convert Hex Code to RGB
    '''
    hex = hex.lstrip("#")
    lv = len(hex)
    return tuple(int(hex[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def Util_RGB2Hex(rgb):
    '''
    Util - Convert RGB to Hex Code
    '''
    return "#%02x%02x%02x" % rgb

def Util_GetTuplePoint(x):
    '''
    Util - Get Point as Integer Tuple
    '''
    return (int(x[0]), int(x[1]))

def VideoUtils_SaveVisualisationVideo(notes, notes_frames, audio_path, save_path, fps=24, initial_frame=None):
    '''
    VideoUtils - Save Note Frames with Audio as Visualisation Video
    '''
    # Init
    AUDIO = AudioFileClip(audio_path)
    DURATION = AUDIO.duration
    FRAMES = []
    FRAMES_INFO = []
    # Form final notes (clean overlapping notes)
    NOTES_FINAL = []
    for i in range(len(notes)):
        cur_note = {
            "note": notes[i]["note"],
            "delay": notes[i]["delay"],
            "duration": notes[i]["duration"] if i == len(notes)-1 else notes[i+1]["delay"]
        }
        NOTES_FINAL.append(cur_note)
    notes = NOTES_FINAL
    # Initial Frame
    if notes[0]["delay"] > 0:
        if initial_frame is None: initial_frame = np.copy(notes_frames[0][0])
        initial_frame_clip = ImageClip(initial_frame).set_duration(notes[0]["delay"])
        FRAMES.append(initial_frame_clip)
        FRAMES_INFO.append({
            "type": "initial",
            "note": notes[0]["note"],
            "duration": notes[0]["delay"]
        })
    # Iterate over notes
    cur_time = 0
    for i in range(len(notes)):
        note_frame_duration = notes[i]["duration"] / len(notes_frames[i])
        for j in range(len(notes_frames[i])):
            frame_clip = ImageClip(notes_frames[i][j]).set_duration(note_frame_duration)
            FRAMES.append(frame_clip)
            FRAMES_INFO.append({
                "type": "note",
                "note": notes[i]["note"],
                "duration": note_frame_duration,
            })
        cur_time += note_frame_duration
    # Final Frames
    if cur_time < DURATION:
        final_frame_clip = ImageClip(notes_frames[-1][-1]).set_duration(DURATION - cur_time)
        FRAMES.append(final_frame_clip)
        FRAMES_INFO.append({
            "type": "final",
            "note": notes[-1]["note"],
            "duration": DURATION - cur_time,
        })
    # Concatenate
    VIDEO = concatenate_videoclips(FRAMES, method="chain")
    # Set Audio
    VIDEO = VIDEO.set_audio(AUDIO)
    # Write Video
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    VIDEO.write_videofile(save_path, fps=fps)

def VideoUtils_CombineVisualisationVideos(video_paths, save_path, compress_size=True, fps=24):
    '''
    VideoUtils - Combine Visualisation Videos
    '''
    # Init
    N = len(video_paths)
    N_ROWS = int(N ** (0.5))
    N_COLS = int(np.ceil(N / N_ROWS))
    VIDEO_GRID = []
    # Combine Videos
    for vi in range(N):
        VIDEO_CLIP = VideoFileClip(video_paths[vi])
        if compress_size: VIDEO_CLIP = VIDEO_CLIP.resize(1/N_COLS)
        if vi % N_COLS == 0:
            VIDEO_GRID.append([VIDEO_CLIP])
        else:
            VIDEO_GRID[-1].append(VIDEO_CLIP)
    COMBINED_VIDEO = clips_array(VIDEO_GRID)
    # Save Combined Video
    COMBINED_VIDEO.write_videofile(save_path, fps=fps)

# Main Functions
def CircleBouncer_VisualiseNotes(notes, UNIQUE_NOTES, frame_size=(1024, 1024),
    mode="line_sequence", # Can be ["line_sequence", "converge_sequence"]
    show_text=True,
    param_percents={
        "gap": 0.1,
        "circle": {
            "thickness": 0.0025
        },
        "text": {
            "scale": 0.0005
        },
        "line": {
            "thickness": 0.0025
        },
        "point": {
            "radius": 0.01
        }
    },
    colors={
        "circle": "#85FFE9",
        "note": {
            "cmap": CMAP_DEFAULT
        }
    }):
    '''
    Circle Bouncer - Visualise Notes

    Parameters:
    - notes: List of notes for the current track (Can visualise only one track at a time)
    - UNIQUE_NOTES: list of possible notes
    - frame_size: Size of visualisation frame
    - mode: Mode/Type of visualisation
        - "line_sequence": At each iteration of notes, draw a line from previous note to current note
        - "converge_lines": At each iteration of notes, draw lines from all seen previous notes to current note
    - show_text: Whether to display the note names as text in the circle or not
    - param_percentages: Parameters to control the sizes and gaps in the visualisation (given as percentage of total size of frame)
    - colors: Parameters to control the colors used in the visualisation
    '''
    # Init
    NOTES_FRAMES = []
    I = np.zeros((frame_size[0], frame_size[1], 3), dtype=np.uint8)
    UNIQUE_NOTES_DATA = {k: {} for k in UNIQUE_NOTES}
    MIN_FRAME_SIZE = min(frame_size[0], frame_size[1])
    ## Set Note Colors
    NOTE_COLORS = {
        "cmap_list": np.array(plt.cm.get_cmap(colors["note"]["cmap"])(np.linspace(0, 1, len(UNIQUE_NOTES)))[:, :3]*255, dtype=int).tolist()
    }
    NOTE_COLORS["color_map"] = {
        UNIQUE_NOTES[i]: tuple(NOTE_COLORS["cmap_list"][i])
        for i in range(len(UNIQUE_NOTES))
    }
    plt.cm.get_cmap("rainbow")
    # Draw initial circle
    GAP = int(MIN_FRAME_SIZE*param_percents["gap"]/2) # Gap between radius of circle and size of frame
    CIRCLE_PARAMS = {
        "center": (int(frame_size[0]/2), int(frame_size[1]/2)),
        "radius": int(min(frame_size[0], frame_size[1])/2 - GAP),
        "color": Util_Hex2RGB(colors["circle"]),
        "thickness": max(1, int(MIN_FRAME_SIZE*param_percents["circle"]["thickness"]))
    }
    I = cv2.circle(
        I, CIRCLE_PARAMS["center"], CIRCLE_PARAMS["radius"],
        CIRCLE_PARAMS["color"], CIRCLE_PARAMS["thickness"]
    )
    I = np.array(I, dtype=np.uint8)
    ## Draw unique notes
    TEXT_PARAMS = {
        "font": cv2.FONT_HERSHEY_SIMPLEX,
        "font_scale": MIN_FRAME_SIZE*param_percents["text"]["scale"],
        "thickness": 0
    }
    for i in range(len(UNIQUE_NOTES)):
        theta = (np.pi*2) / len(UNIQUE_NOTES)
        angle = theta*i
        point = (
            CIRCLE_PARAMS["center"][0] + CIRCLE_PARAMS["radius"]*np.cos(angle), 
            CIRCLE_PARAMS["center"][1] + CIRCLE_PARAMS["radius"]*np.sin(angle)
        )
        if show_text:
            TEXT_PARAMS["color"] = NOTE_COLORS["color_map"][UNIQUE_NOTES[i]]
            I = cv2.putText(
                I, str(UNIQUE_NOTES[i]), Util_GetTuplePoint(point),
                TEXT_PARAMS["font"], TEXT_PARAMS["font_scale"],
                TEXT_PARAMS["color"], TEXT_PARAMS["thickness"], cv2.LINE_AA
            )
            I = np.array(I, dtype=np.uint8)
        UNIQUE_NOTES_DATA[UNIQUE_NOTES[i]] = {
            "index": i,
            "position": point
        }
    # Draw Notes
    LINE_PARAMS = {
        "thickness": max(1, int(MIN_FRAME_SIZE*param_percents["line"]["thickness"]))
    }
    POINT_PARAMS = {
        "radius": max(1, int(MIN_FRAME_SIZE*param_percents["point"]["radius"])),
        "thickness": -1
    }
    cur_data = {
        "note": None,
        "position": (0, 0)
    }
    for i in range(len(notes)):
        note_frames = []
        if cur_data["note"] is not None:
            ## Set Line Color as destination note color
            LINE_PARAMS["color"] = NOTE_COLORS["color_map"][notes[i]["note"]]
            ## Draw Line
            I = cv2.line(
                I,
                Util_GetTuplePoint(cur_data["position"]), 
                Util_GetTuplePoint(UNIQUE_NOTES_DATA[notes[i]["note"]]["position"]),
                LINE_PARAMS["color"], LINE_PARAMS["thickness"]
            )
            I = np.array(I, dtype=np.uint8)
        cur_data["note"] = notes[i]["note"]
        cur_data["position"] = UNIQUE_NOTES_DATA[notes[i]["note"]]["position"]
        ## Set Point Color destination note color
        POINT_PARAMS["color"] = NOTE_COLORS["color_map"][cur_data["note"]]
        ## Draw Point
        I_withpoint = np.copy(I)
        I_withpoint = cv2.circle(
            I_withpoint, Util_GetTuplePoint(cur_data["position"]),
            POINT_PARAMS["radius"], POINT_PARAMS["color"], POINT_PARAMS["thickness"]
        )
        I_withpoint = np.array(I_withpoint, dtype=np.uint8)
        note_frames.append(I_withpoint)
        NOTES_FRAMES.append(note_frames)
    
    return NOTES_FRAMES


# RunCode