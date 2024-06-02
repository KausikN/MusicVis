"""
Visualiser Library - Circle Bouncer
"""

# Imports
import os
import cv2
import json
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
    NOTES_FRAMES_FINAL = []
    for i in range(len(notes)):
        cur_note = {
            "note": notes[i]["note"],
            "delay": notes[i]["delay"],
            "duration": notes[i]["duration"] if i == len(notes)-1 else notes[i+1]["delay"]
        }
        ## If cur note starts at same time as previous note (delay = 0)
        if len(notes_frames[i]) > 0:
            NOTES_FINAL.append(cur_note)
            NOTES_FRAMES_FINAL.append(notes_frames[i])
    notes = NOTES_FINAL
    notes_frames = NOTES_FRAMES_FINAL
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
                "video_duration": FRAMES[-1].duration
            })
        cur_time += notes[i]["duration"]
    # Final Frames
    if cur_time < DURATION:
        final_frame_clip = ImageClip(notes_frames[-1][-1]).set_duration(DURATION - cur_time)
        FRAMES.append(final_frame_clip)
        FRAMES_INFO.append({
            "type": "final",
            "note": notes[-1]["note"],
            "duration": DURATION - cur_time,
            "video_duration": FRAMES[-1].duration
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
def CircleBouncer_VisualiseMode_LineSequence(notes, cur_data, **params):
    '''
    Circle Bouncer - Visualise Mode - Line Sequence
    '''
    # Init
    iteration = cur_data["iteration"]
    I = np.copy(cur_data["I"])
    note = notes[iteration]
    UNIQUE_NOTES_DATA = params["UNIQUE_NOTES_DATA"]
    NOTE_COLORS = params["NOTE_COLORS"]
    LINE_PARAMS = params["LINE_PARAMS"]
    POINT_PARAMS = params["POINT_PARAMS"]
    FRAMES_PER_NOTE = params["frames_per_note"]
    next_data = {
        "note": note["note"],
        "position": UNIQUE_NOTES_DATA[note["note"]]["position"]
    }
    note_frames = [np.copy(I)]

    # For non-first iterations, draw line
    if "notes" in cur_data.keys():
        note_frames = []
        ## Draw lines from source point to destination for each iteration till now (within fade threshold of current iteration)
        start_it = max(0, iteration-NOTE_COLORS["fade_threshold"]+1) if NOTE_COLORS["fade_threshold"] > 0 else 0
        for ci in range(start_it, iteration-1):
            ### Init
            source = cur_data["notes"][ci]
            destination = cur_data["notes"][ci+1]
            ### Set Line Color as destination note color with fade
            if NOTE_COLORS["fade_threshold"] > 0:
                LINE_PARAMS["color"] = NOTE_COLORS["color_map_withfade"][destination["note"]][iteration-ci]
            else:
                LINE_PARAMS["color"] = NOTE_COLORS["color_map"][destination["note"]]
            ### Draw Line
            I = cv2.line(
                I,
                Util_GetTuplePoint(source["position"]), 
                Util_GetTuplePoint(destination["position"]), 
                LINE_PARAMS["color"], LINE_PARAMS["thickness"]
            )
        ## Draw line for current iteration (with FRAMES_PER_NOTE-1 intermediate lines)
        LINE_PARAMS["color"] = NOTE_COLORS["color_map"][next_data["note"]]
        start_pos = np.array(cur_data["notes"][-1]["position"])
        end_pos = np.array(next_data["position"])
        cur_start_pos = start_pos
        cur_end_pos = start_pos
        diff_pos = end_pos - start_pos
        for fi in range(FRAMES_PER_NOTE):
            cur_start_pos = cur_end_pos
            cur_end_pos = cur_start_pos + (diff_pos / FRAMES_PER_NOTE)
            I = cv2.line(
                I,
                Util_GetTuplePoint(cur_start_pos),
                Util_GetTuplePoint(cur_end_pos),
                LINE_PARAMS["color"], LINE_PARAMS["thickness"]
            )
            I = np.array(I, dtype=np.uint8)
            note_frames.append(np.copy(I))
    else:
        cur_data.update({
            "notes": []
        })

    # For all iterations, draw point
    ## Set Point Color destination note color
    POINT_PARAMS["color"] = NOTE_COLORS["color_map"][next_data["note"]]
    ## Draw Point
    I_last = cv2.circle(
        note_frames[-1], Util_GetTuplePoint(next_data["position"]),
        POINT_PARAMS["radius"], POINT_PARAMS["color"], POINT_PARAMS["thickness"]
    )
    I_last = np.array(I_last, dtype=np.uint8)
    note_frames[-1] = I_last

    # Update Cur Data
    cur_data["notes"].append(next_data)

    return note_frames, cur_data

def CircleBouncer_VisualiseMode_ConvergeSequence(notes, cur_data, **params):
    '''
    Circle Bouncer - Visualise Mode - Converge Sequence
    '''
    # Init
    iteration = cur_data["iteration"]
    I = np.copy(cur_data["I"])
    note = notes[iteration]
    UNIQUE_NOTES_DATA = params["UNIQUE_NOTES_DATA"]
    NOTE_COLORS = params["NOTE_COLORS"]
    LINE_PARAMS = params["LINE_PARAMS"]
    POINT_PARAMS = params["POINT_PARAMS"]
    next_data = {
        "note": note["note"],
        "position": UNIQUE_NOTES_DATA[note["note"]]["position"]
    }
    note_frames = [np.copy(I)]

    # For non-first iterations, draw converging lines
    if "notes" in cur_data.keys():
        note_frames = []
        ## Draw line from each visited note to current destination note (within fade threshold of current iteration)
        start_it = max(0, iteration-NOTE_COLORS["fade_threshold"]+1) if NOTE_COLORS["fade_threshold"] > 0 else 0
        for pi in range(start_it, iteration-1):
            source = cur_data["notes"][pi]
            ### Set Line Color as source note color with fade
            if NOTE_COLORS["fade_threshold"] > 0:
                LINE_PARAMS["color"] = NOTE_COLORS["color_map_withfade"][source["note"]][iteration-pi]
            else:
                LINE_PARAMS["color"] = NOTE_COLORS["color_map"][source["note"]]
            ### Draw Line
            I = cv2.line(
                I,
                Util_GetTuplePoint(source["position"]), 
                Util_GetTuplePoint(next_data["position"]),
                LINE_PARAMS["color"], LINE_PARAMS["thickness"]
            )
        I = np.array(I, dtype=np.uint8)
        note_frames.append(np.copy(I))
    else:
        cur_data.update({
            "notes": []
        })

    # For all iterations, draw point
    ## Set Point Color destination note color
    POINT_PARAMS["color"] = NOTE_COLORS["color_map"][next_data["note"]]
    ## Draw Point
    I_last = cv2.circle(
        note_frames[-1], Util_GetTuplePoint(next_data["position"]),
        POINT_PARAMS["radius"], POINT_PARAMS["color"], POINT_PARAMS["thickness"]
    )
    I_last = np.array(I_last, dtype=np.uint8)
    note_frames[-1] = I_last

    # Update Cur Data
    cur_data["notes"].append(next_data)

    return note_frames, cur_data

def CircleBouncer_VisualiseNotes(notes, UNIQUE_NOTES, frame_size=(1024, 1024),
    mode="line_sequence", # Can be ["line_sequence", "converge_lines"]
    show_text=True, frames_per_notesec=1,
    fade_params={
        "type": "none",
        "threshold": 5
    },
    sizes={
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
    },
    PROGRESS_BAR=None
    ):
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
    - frames_per_notesec: Number of frames per second for each note
    - fade_params: Fading parameters
        - "type": Type of fading applied to fade out the lines of previous notes
            - "none": No fade out
            - "linear": Linearly fade out previous notes based on difference between current iteration and iteration of the note
        - "threshold": Threshold beyond which if the iteration difference exceeds, the note line is not displayed
    - sizes: Parameters to control the sizes and gaps in the visualisation (given as percentage of total size of frame)
    - colors: Parameters to control the colors used in the visualisation
    '''
    # Init
    NOTES_FRAMES = []
    I = np.zeros((frame_size[0], frame_size[1], 3), dtype=np.uint8)
    UNIQUE_NOTES_DATA = {k: {} for k in UNIQUE_NOTES}
    MIN_FRAME_SIZE = min(frame_size[0], frame_size[1])
    ## Set Note Colors
    NOTE_COLORS = {
        "fade_threshold": fade_params["threshold"],
        "background": Util_Hex2RGB(colors["circle"]) if sizes["circle"]["thickness"] == -1 else Util_Hex2RGB("#000000"),
        "cmap_list": np.array(plt.get_cmap(colors["note"]["cmap"])(np.linspace(0, 1, len(UNIQUE_NOTES)))[:, :3]*255, dtype=int).tolist()
    }
    NOTE_COLORS["color_map"] = {
        UNIQUE_NOTES[i]: tuple(NOTE_COLORS["cmap_list"][i])
        for i in range(len(UNIQUE_NOTES))
    }
    NOTE_COLORS["color_map_withfade"] = {}
    bg_color = np.array(NOTE_COLORS["background"])
    for un in UNIQUE_NOTES:
        NOTE_COLORS["color_map_withfade"][un] = []
        if fade_params["threshold"] > 0:
            note_color = np.array(NOTE_COLORS["color_map"][un])
            for itd in range(fade_params["threshold"]):
                cur_faded_color = note_color
                if fade_params["type"] == "linear":
                    cur_faded_color = (itd*bg_color + (fade_params["threshold"]-itd)*note_color) / fade_params["threshold"]
                    cur_faded_color = np.array(np.round(cur_faded_color, 0), dtype=np.uint8)
                cur_faded_color = tuple(cur_faded_color.tolist())
                NOTE_COLORS["color_map_withfade"][un].append(cur_faded_color)
    # Draw initial circle
    GAP = int(MIN_FRAME_SIZE*sizes["gap"]/2) # Gap between radius of circle and size of frame
    CIRCLE_PARAMS = {
        "center": (int(frame_size[0]/2), int(frame_size[1]/2)),
        "radius": int(min(frame_size[0], frame_size[1])/2 - GAP),
        "color": Util_Hex2RGB(colors["circle"]),
        "thickness": max(1, int(MIN_FRAME_SIZE*sizes["circle"]["thickness"]))
    }
    I = cv2.circle(
        I, CIRCLE_PARAMS["center"], CIRCLE_PARAMS["radius"],
        CIRCLE_PARAMS["color"], CIRCLE_PARAMS["thickness"]
    )
    I = np.array(I, dtype=np.uint8)
    ## Draw unique notes
    TEXT_PARAMS = {
        "font": cv2.FONT_HERSHEY_SIMPLEX,
        "font_scale": MIN_FRAME_SIZE*sizes["text"]["scale"],
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
        "thickness": max(1, int(MIN_FRAME_SIZE*sizes["line"]["thickness"]))
    }
    POINT_PARAMS = {
        "radius": max(1, int(MIN_FRAME_SIZE*sizes["point"]["radius"])),
        "thickness": -1
    }
    cur_data = {
        "iteration": 0,
        "I": I
    }
    if PROGRESS_BAR is not None: PROGRESS_BAR.setTotal(len(notes))
    for i in range(len(notes)):
        cur_data["iteration"] = i
        note_frames = []

        if mode == "line_sequence":
            note_frames, cur_data = CircleBouncer_VisualiseMode_LineSequence(
                notes, cur_data,
                UNIQUE_NOTES_DATA=UNIQUE_NOTES_DATA, NOTE_COLORS=NOTE_COLORS,
                LINE_PARAMS=LINE_PARAMS, POINT_PARAMS=POINT_PARAMS,
                frames_per_note=max(1, int(round(frames_per_notesec*notes[i]["duration"])))
            )
        elif mode == "converge_lines":
            note_frames, cur_data = CircleBouncer_VisualiseMode_ConvergeSequence(
                notes, cur_data,
                UNIQUE_NOTES_DATA=UNIQUE_NOTES_DATA, NOTE_COLORS=NOTE_COLORS,
                LINE_PARAMS=LINE_PARAMS, POINT_PARAMS=POINT_PARAMS
            )

        NOTES_FRAMES.append(note_frames)
        if PROGRESS_BAR is not None: PROGRESS_BAR.next()
    if PROGRESS_BAR is not None: PROGRESS_BAR.close()

    return NOTES_FRAMES


# RunCode