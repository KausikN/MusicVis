"""
Visualiser Library - MIDI Plot
"""

# Imports
import numpy as np
import matplotlib.pyplot as plt

# Main Vars


# Main Functions
def MIDIPlot_PlotNotes_HBar(notes, note_value_name_map=None, note_value_color_map=None, start_time=0):
    '''
    MIDI Plot - Plot Notes as Horizontal Bar Graph

    X axis is time and Y axis is the different possible note values
    '''
    # Init Maps
    VALUE_MAP = {}
    VALUE_NAMES = []
    if note_value_name_map is None:
        unique_note_values = sorted(list(set([note["value"] for note in notes])))
        for i in range(len(unique_note_values)):
            VALUE_MAP[unique_note_values[i]] = {
                "name": str(i),
                "index": i
            }
        VALUE_NAMES = [VALUE_MAP[v]["name"] for v in unique_note_values]
    else:
        unique_note_values = sorted(list(note_value_name_map.keys()))
        for i in range(len(unique_note_values)):
            VALUE_MAP[unique_note_values[i]] = {
                "name": str(note_value_name_map[unique_note_values[i]]),
                "index": i
            }
        VALUE_NAMES = [VALUE_MAP[v]["name"] for v in unique_note_values]
    # Init Colors
    unique_note_values = sorted(list(VALUE_MAP.keys()))
    if note_value_color_map is None:
        DEFAULT_COLORS = [
            "red", "maroon", "lightgreen", "darkgreen",
            "lightblue", "indigo", "gray", "black",
            "violet", "purple", "pink", "orange"
        ]
        note_value_color_map = {}
        for i in range(len(unique_note_values)): note_value_color_map[unique_note_values[i]] = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]

    # Form rectangles from notes
    Y = [VALUE_MAP[note["value"]]["index"] for note in notes]
    X_left = []
    X_width = []
    X_color = []
    cur_left = start_time
    for note in notes:
        cur_left += note["delay"]
        X_left.append(cur_left)
        X_width.append(note["duration"])
        X_color.append(note_value_color_map[note["value"]])
    # Plot
    FIG = plt.figure()
    # plt.title("MIDI")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Notes")
    plt.yticks(list(range(len(VALUE_NAMES))), VALUE_NAMES)
    AX = plt.barh(np.array(Y), width=np.array(X_width), left=np.array(X_left), color=X_color)
    plt.grid(True, linestyle="--")
    ## Close figure
    plt.close()

    return FIG


# RunCode
